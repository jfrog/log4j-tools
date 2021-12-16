import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class Main {
    enum JndiManagerVersion {
        v214_OR_BELOW,
        v215,
        v216_OR_ABOVE
    }
    static final private String CLASS_NAME = "log4j/core/net/JndiManager.class";
    static final private String PATCH_STRING = "allowedJndiProtocols";
    static final private String PATCH_STRING_216 = "log4j2.enableJndi";
    static final private String GREEN = "\u001b[32m";
    static final private String RED = "\u001b[31m";
    static final private String RESET_ALL = "\u001b[0m";

    public static List<Path> listFiles(Path path) throws IOException {
        try (Stream<Path> walk = Files.walk(path)) {
            return walk.filter(Files::isRegularFile)
                    .collect(Collectors.toList());
        }
    }

    private static JndiManagerVersion checkClass(byte[] class_content) {
        String buf_string = new String(class_content, StandardCharsets.UTF_8);
        if (buf_string.contains(PATCH_STRING)) {
            if (buf_string.contains(PATCH_STRING_216)) {
                return JndiManagerVersion.v216_OR_ABOVE;
            }
            return JndiManagerVersion.v215;
        }
        return JndiManagerVersion.v214_OR_BELOW;
    }

    private static void printVersionMessage(String path, JndiManagerVersion version) {
        switch (version) {
            case v214_OR_BELOW:
                System.out.println(path + ":"+ RED + " vulnerable JndiManager found" + RESET_ALL);
                break;
            case v215:
                System.out.println(path + ":"+ GREEN + " fixed JndiManager found" + RESET_ALL + " (2.15)");
                break;
            case v216_OR_ABOVE:
                System.out.println(path + ":"+ GREEN + " fixed JndiManager found" + RESET_ALL);
        }

    }

    private static void analyzeFileName(Path path, String root_dir) {
        Path pathRelative = Paths.get(root_dir).relativize(path);
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(path.toString()))) {
            analyzeFile(bis, pathRelative.toString());
        } catch (IOException e) {
            //
        }
    }

    private static void analyzeFile(InputStream stream, String relativePath) throws IOException {
        ZipEntry entry;
        ZipInputStream zipInputStream = new ZipInputStream(stream);
        try {
            while ((entry = zipInputStream.getNextEntry()) != null) {
                if (entry.getName().endsWith(".jar")) {
                    analyzeFile(zipInputStream, relativePath + "/" + entry.getName());
                } else {
                    if (entry.getName().endsWith(CLASS_NAME)) {
                        printVersionMessage(relativePath, checkClass(zipInputStream.readAllBytes()));
                    }
                }
            }
        } catch (IOException e) {
            //
        }
        zipInputStream.closeEntry();
        // zipInputStream not closed in order not to rewind the higher level stream
    }

    private static boolean acceptableFile(String filename) {
        return filename.endsWith(".jar") || filename.endsWith(".war");
    }

    private static void runScan(String root_folder) throws IOException{
        System.out.println("Scanning...");
        File f = new File(root_folder);
        if (f.isDirectory()) {
            Path path = Paths.get(root_folder);
            List<Path> paths = listFiles(path);
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
        if (args.length != 1) {
            System.out.println("Usage: scan_jndimanager_versions.jar <root_folder>");
        } else {
            try{
                runScan(args[0]);
            }
            catch (IOException e) {
                System.out.println("Cannot list directory");
            }
        }
    }
}