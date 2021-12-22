import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class Main {

    static final private String GREEN = "\u001b[32m";
    static final private String RED = "\u001b[31m";
    static final private String YELLOW = "\u001b[33m";
    static final private String RESET_ALL = "\u001b[0m";
    private static boolean configFileFound = false;

    public static List<Path> listFiles(Path path) throws IOException {
        try (Stream<Path> walk = Files.walk(path)) {
            return walk.filter(Files::isRegularFile)
                    .collect(Collectors.toList());
        }
    }

    private static void applicMessage(String path, boolean applicable) {
        String msg;
        if (applicable) {
            msg = RED + "applicable" + RESET_ALL;
        } else {
            msg =GREEN + "not applicable" + RESET_ALL;
        }
        System.out.println("\n\n" + path + ":\n\tFor this configuration, CVE-2021-45046 is " + msg);
    }

    private static void analyzeArchiveFileName(Path path, String root_dir) {
        Path pathRelative = Paths.get(root_dir).relativize(path);
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(path.toString()))) {
            analyzeJarFile(bis, pathRelative.toString());
        } catch (IOException e) {
            //
        }
    }


    private static void analyzeConfigFileName(Path path, String root_dir) {
        String pathRelative = Paths.get(root_dir).relativize(path).toString();
        try (BufferedInputStream bis = new BufferedInputStream(new FileInputStream(path.toString()))) {
            applicableConfigFile(bis, pathRelative);
            configFileFound = true;
        } catch (IOException e) {
            //
        }
    }

    private static boolean configurationFileMaybe(String path) {
        String filename = path.substring(path.lastIndexOf('/') + 1);
        if (! (filename.startsWith("log4j2.") || filename.startsWith("log4j2-test."))) {
            return false;
        }
        if (filename.indexOf('.') != filename.lastIndexOf('.')) {
            return false;
        }
        return filename.endsWith(".properties") ||
                filename.endsWith(".yaml") ||
                filename.endsWith(".yml") ||
                filename.endsWith(".json") ||
                filename.endsWith(".jsn") ||
                filename.endsWith(".xml");
    }

    private static void printConfigLine(int lineIndex, String configLine) {
        System.out.printf(GREEN +"%d\t" + RESET_ALL, lineIndex);
        System.out.printf("%s\n", configLine);
    }

    private static void applicableConfigFile(InputStream stream, String relativePath) throws IOException{
        BufferedReader br = new BufferedReader(new InputStreamReader(stream));
        String strLine;
        String comment = null;
        boolean firstResultInFile = true;
        int lineCount = 0;

        if (relativePath.endsWith(".xml")) {
            comment = "<--";
        } else
            if (relativePath.endsWith(".yml") ||
                relativePath.endsWith(".yaml") ||
                relativePath.endsWith(".properties")) {
                comment = "#";
            }
        while ((strLine = br.readLine()) != null)   {
            lineCount ++;
            if (comment != null && strLine.contains(comment)) {
                strLine = strLine.substring(0, strLine.indexOf(comment));
            }
            if (strLine.contains("${ctx:") || strLine.contains("${sd:") || strLine.contains("${map:")) {
                if (firstResultInFile) {
                    firstResultInFile = false;
                    applicMessage(relativePath, true);
                    System.out.println("Evidence:");
                }
                printConfigLine(lineCount, strLine);
            }
        }
        if (firstResultInFile)
            applicMessage(relativePath, false);
    }

    private static void analyzeJarFile(InputStream stream, String relativePath) throws IOException {
        ZipEntry entry;
        ZipInputStream zipInputStream = new ZipInputStream(stream);
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
                if (acceptableArchiveFile(entry.getName())) {
                    analyzeJarFile(zipInputStream, relativePath + "/" + entry.getName());
                } else {
                    String filename = entry.getName();
                    if (configurationFileMaybe(filename)) {
                        String configFile = relativePath + "/" + filename;
                        applicableConfigFile(zipInputStream, configFile);
                        configFileFound = true;
                    }
                }
            }
        } catch (IOException e) {
            //
        }
        zipInputStream.closeEntry();
        // zipInputStream not closed in order not to rewind the higher level stream
    }

    private static boolean acceptableArchiveFile(String filename) {
        return filename.endsWith(".jar") || filename.endsWith(".war") ||
               filename.endsWith(".ear") || filename.endsWith(".sar");
    }

    private static void runScan(String root_folder) throws IOException{
        System.out.println("Scanning...");
        File f = new File(root_folder);
        if (f.isDirectory()) {
            Path path = Paths.get(root_folder);
            List<Path> paths = listFiles(path);
            paths.stream().
                    filter(x -> acceptableArchiveFile(x.toString())).
                    forEach(x -> analyzeArchiveFileName(x, root_folder));
            paths.stream().
                    filter(x -> configurationFileMaybe(x.toString())).
                    forEach(x -> analyzeConfigFileName(x, root_folder));

        } else {
            if (f.isFile()) {
                if (acceptableArchiveFile(root_folder)) {
                    analyzeArchiveFileName(Paths.get(root_folder), root_folder);
                }
            }
        }
        if (!configFileFound) {
            System.out.println(YELLOW + "Could not find log4j configuration file, result is inconclusive" + RESET_ALL);
        }

    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.out.println("Usage: scan_cve_2021_45046_config.jar <root_folder>");
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