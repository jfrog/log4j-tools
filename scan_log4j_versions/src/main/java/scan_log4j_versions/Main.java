import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class Main {
    enum JndiManagerVersion {
        NOT_FOUND,
        v20_v214,
        v215,
        v216,
        v217,
        v212_PATCH,
    }

    enum JndiLookupVersion {
        NOT_FOUND,
        v20,
        v21_PLUS,
        v212_PATCH,
    }

    enum Status {
        INCONSISTENT,
        VULN,
        PARTIAL,
        FIXED
    }

    static class Diag {
        public Status status;
        public String note;
        Diag(Status initStatus, String initNote) {
            status = initStatus;
            note = initNote;
        }
    }

    static final private String CLASS_NAME_JNDI_MANAGER = "core/net/JndiManager.class";
    static final private String CLASS_NAME_JNDI_LOOKUP = "core/lookup/JndiLookup.class";
    static final private String PATCH_STRING = "allowedJndiProtocols";
    static final private String PATCH_STRING_216 = "log4j2.enableJndi";
    static final private String PATCH_STRING_21 = "LOOKUP";
    static final private String PATCH_STRING_BACKPORT = "JNDI is not supported";
    static final private String PATCH_STRING_217 = "isJndiLookupEnabled";

    static final private String GREEN = "\u001b[32m";
    static final private String RED = "\u001b[31m";
    static final private String YELLOW = "\u001b[33m";
    static final private String RESET_ALL = "\u001b[0m";

    private static boolean notExcludedDir(Path path, List<Path> excluded) {
        for (Path excludedPath: excluded) {
            if (path.startsWith(excludedPath)) {
                return false;
            }
        }
        return true;
    }

    private static List<Path> listFiles(Path path, List<Path> excludedDirs) throws IOException {
        try (Stream<Path> walk = Files.walk(path)) {
            return walk.filter(Files::isRegularFile).filter(x -> notExcludedDir(x, excludedDirs))
                    .collect(Collectors.toList());
        }
    }

    private static void versionMessage(String path, Diag diagnosis) {
        String msg = "";
        switch (diagnosis.status) {
            case FIXED:
                msg = GREEN + "fixed" + RESET_ALL;
                break;
            case PARTIAL:
                msg = YELLOW + "mitigated" + RESET_ALL;
                break;
            case VULN:
                msg = RED + "vulnerable" + RESET_ALL;
                break;
            case INCONSISTENT:
                msg = RED + "inconsistent"  + RESET_ALL;
        }
        System.out.println(path + ": " + msg + " " + diagnosis.note);
    }

    private static JndiManagerVersion getJndiManagerVersion(byte[] class_content) {
        String buf_string = new String(class_content, StandardCharsets.UTF_8);
        if (buf_string.contains(PATCH_STRING)) {
            if (buf_string.contains(PATCH_STRING_216)) {
                return JndiManagerVersion.v216;
            }
            return JndiManagerVersion.v215;
        } else {
            if (buf_string.contains(PATCH_STRING_216)) {
                if (buf_string.contains(PATCH_STRING_217)) {
                    return JndiManagerVersion.v217;
                } else {
                    return JndiManagerVersion.v212_PATCH;
                }
            }
        }
        return JndiManagerVersion.v20_v214;
    }


    private static JndiLookupVersion getJndiLookupVersion(byte[] class_content) {
        String buf_string = new String(class_content, StandardCharsets.UTF_8);
        if (buf_string.contains(PATCH_STRING_21)) {
            return JndiLookupVersion.v21_PLUS;
        }
        if (buf_string.contains(PATCH_STRING_BACKPORT)) {
            return JndiLookupVersion.v212_PATCH;
        }
        return JndiLookupVersion.v20;
    }

    private static void confusionMessage(String relPath, String duplicateClass) {
        System.out.println("Warning: " + relPath + " contains multiple copies of " + duplicateClass);
    }

    private static void analyzeFileName(Path path, String root_dir) {
        Path pathRelative = Paths.get(root_dir).relativize(path);
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(path.toString()))) {
            analyzeFile(bis, pathRelative.toString());
        } catch (IOException e) {
            //
        }
    }

    private static Diag getDiagnosis(JndiLookupVersion lookupVersion, JndiManagerVersion managerVersion) {
        switch (lookupVersion) {
            case NOT_FOUND:
                return new Diag(Status.FIXED, "JndiLookup removed");
            case v20:
                if (managerVersion == JndiManagerVersion.NOT_FOUND) {
                    return new Diag(Status.VULN, "Estimated version: 2.0");
                }
                break;
            case v212_PATCH:
                if (managerVersion == JndiManagerVersion.v212_PATCH) {
                    return new Diag(Status.FIXED, "Estimated version: 2.12.2 backport patch");
                }
                break;
            case v21_PLUS:
                switch (managerVersion) {
                    case v20_v214:
                        return new Diag(Status.VULN, "Estimated version: 2.1 .. 2.14");
                    case v215:
                        return new Diag(Status.PARTIAL, "Estimated version: 2.15");
                    case v216:
                        return new Diag(Status.FIXED, "Estimated version: 2.16");
                    case v217:
                        return new Diag(Status.FIXED, "Estimated version: 2.17");

                }
        }
        return new Diag(Status.INCONSISTENT, "JndiLookup: " + lookupVersion +
                ", JndiManager: " + managerVersion);
    }

    private static byte[] readAllBytes(InputStream inputStream) throws IOException {
        final int bufLen = 1024;
        byte[] buf = new byte[bufLen];
        int readLen;

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        while ((readLen = inputStream.read(buf, 0, bufLen)) != -1) {
            outputStream.write(buf, 0, readLen);

        }
        return outputStream.toByteArray();
    }

    private static void analyzeFile(InputStream stream, String relativePath) throws IOException {
        ZipEntry entry;
        ZipInputStream zipInputStream = new ZipInputStream(stream);
        JndiManagerVersion managerVersion = JndiManagerVersion.NOT_FOUND;
        JndiLookupVersion lookupVersion = JndiLookupVersion.NOT_FOUND;
        try {
            while (true) {
                try {
                    entry = zipInputStream.getNextEntry();
                    if (entry == null) {
                        break;
                    }
                }
                catch (IllegalArgumentException  e) {
                    continue;
                }

                if (acceptableFile(entry.getName())) {
                    analyzeFile(zipInputStream, relativePath + "/" + entry.getName());
                } else {
                    if (entry.getName().endsWith(CLASS_NAME_JNDI_MANAGER)) {
                        if (managerVersion != JndiManagerVersion.NOT_FOUND) {
                            confusionMessage(relativePath, CLASS_NAME_JNDI_MANAGER);
                        }
                        managerVersion = getJndiManagerVersion(readAllBytes(zipInputStream));
                        continue;
                    }
                    if (entry.getName().endsWith(CLASS_NAME_JNDI_LOOKUP)) {
                        if (lookupVersion != JndiLookupVersion.NOT_FOUND) {
                            confusionMessage(relativePath, CLASS_NAME_JNDI_LOOKUP);
                        }
                        lookupVersion = getJndiLookupVersion(readAllBytes(zipInputStream));

                    }
                }
            }
        } catch (IOException e) {
            //
        }
        zipInputStream.closeEntry();
        // zipInputStream not closed in order not to rewind the higher level stream
        if (lookupVersion != JndiLookupVersion.NOT_FOUND || managerVersion != JndiManagerVersion.NOT_FOUND) {
            Diag diagnosis = getDiagnosis(lookupVersion, managerVersion);
            versionMessage(relativePath, diagnosis);
        }

    }

    private static boolean acceptableFile(String filename) {
        return filename.endsWith(".jar") || filename.endsWith(".war") ||
               filename.endsWith(".ear") || filename.endsWith(".sar") || 
               filename.endsWith(".zip") || filename.endsWith(".par");
    }

    private static void runScan(String root_folder, List<Path> excludedDirs) throws IOException{
        File f = new File(root_folder);
        if (f.isDirectory()) {
            Path path = Paths.get(root_folder);
            List<Path> paths = listFiles(path, excludedDirs);
            paths.stream().
                    filter(x -> acceptableFile(x.toString())).
                    forEach(x -> analyzeFileName(x, root_folder));
        } else {
            if (f.isFile()) {
                if (acceptableFile(root_folder)) {
                    analyzeFileName(Paths.get(root_folder), root_folder);
                }
            }
        }

    }

    public static void main(String[] args) {
        String rootPath = "";
        List<Path> excludedFolders = new ArrayList<>();
        if (args.length == 1 ) {
            rootPath = args[0];
        } else {
            if (args.length > 2 && args[1].equals("-exclude")) {
                rootPath = args[0];
                for (int index=2; index < args.length; index++) {
                    excludedFolders.add(Paths.get(args[index]));
                }
            } else {
                System.out.println("Usage: scan_jndimanager_versions.jar <root_folder> [-exclude <folder1> <folder2> ...]");
            }
        }
        try{
            runScan(rootPath, excludedFolders);
        }
        catch (IOException e) {
            System.out.println("Cannot list directory");
        }
    }
}