package log4shell_xray_wrapper;

import org.apache.commons.io.IOUtils;
import org.apache.maven.artifact.versioning.ComparableVersion;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;

public class JFrogCLI {
    private final String executable;
    private final boolean verbose;

    private static final ComparableVersion minVersion = new ComparableVersion("2.6.2");

    public static class JFrogCLIException extends Exception {
        public JFrogCLIException() {}

        public JFrogCLIException(String message) {
            super(message);
        }
    }

    public static class NoDefaultServer extends JFrogCLIException {}

    public static class Missing extends JFrogCLIException {
        public Missing() {
            super("No JFrog CLI executable found.");
        }
    }

    public static class WrongVersion extends JFrogCLIException {
        ComparableVersion version;

        public WrongVersion(ComparableVersion version) {
            super(
                    "Version "
                            + minVersion
                            + " or higher required, but found "
                            + version.toString()
                            + ".");
            this.version = version;
        }
    }

    public JFrogCLI(boolean verbose) throws Missing, WrongVersion, NoDefaultServer {
        this.verbose = verbose;
        this.executable = findJfrogExecutable();
        ensureJfrogConfiguration();
    }

    private void ensureJfrogConfiguration() throws NoDefaultServer {
        Process process;
        String stdout;
        try {
            process = new ProcessBuilder().command(executable, "config", "show").start();
            stdout = IOUtils.toString(process.getInputStream(), StandardCharsets.UTF_8);

        } catch (IOException e) {
            throw new NoDefaultServer();
        }

        Pattern defaultPattern = Pattern.compile("^Default:\\s+true", Pattern.MULTILINE);
        Pattern xrayUrlPattern = Pattern.compile("^Xray URL:\\s+\\S", Pattern.MULTILINE);
        boolean hasXrayUrl =
                Arrays.stream(stdout.split("Server ID:"))
                        .filter(line -> defaultPattern.matcher(line).find())
                        .anyMatch(line -> xrayUrlPattern.matcher(line).find());

        if (!hasXrayUrl) {
            throw new NoDefaultServer();
        }
    }

    private static String findJfrogExecutable() throws WrongVersion, Missing {
        String executable = null;
        for (String command : new String[] {"jf", "jfrog"}) {
            try {
                Process process = new ProcessBuilder().command(command, "--version").start();
                String stdout = IOUtils.toString(process.getInputStream(), StandardCharsets.UTF_8);
                if (process.waitFor() != 0) {
                    continue;
                }
                String[] versionSplit = stdout.split("version ");
                if (versionSplit.length != 2) {
                    continue;
                }
                ComparableVersion version = new ComparableVersion(versionSplit[1]);
                if (minVersion.compareTo(version) > 0) {
                    throw new WrongVersion(version);
                }
                executable = command;
                break;
            } catch (IOException | InterruptedException ignored) {
            }
        }

        if (executable == null) {
            throw new Missing();
        }
        return executable;
    }

    private List<String> getCves(String scanOutput) {
        ScanResults[] results = ScanResults.fromJson(scanOutput);
        List<String> cves = new ArrayList<>();

        for (ScanResults result : results) {
            for (ScanResults.VulnerabilityInfo vuln : result.vulns) {
                for (ScanResults.CveInfo cve : vuln.cves) {
                    if (cve.cve != null) {
                        cves.add(cve.cve);
                    }
                }
            }
        }
        return cves;
    }

    private List<String> auditForCves(File root, String auditCommand) {
        try {
            Process process =
                    new ProcessBuilder()
                            .command(executable, auditCommand, "--format", "json")
                            .directory(root)
                            .redirectError(
                                    verbose
                                            ? ProcessBuilder.Redirect.INHERIT
                                            : ProcessBuilder.Redirect.DISCARD)
                            .start();

            String stdout = IOUtils.toString(process.getInputStream(), StandardCharsets.UTF_8);
            if (process.waitFor() != 0) {
                System.err.println(
                        "ERROR: Failed running JFrog CLI. Run with --verbose for more details.");
                return List.of();
            }
            return getCves(stdout);

        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }
        return List.of();
    }

    public List<String> AuditGradle(File root) {
        return auditForCves(root, "audit-gradle");
    }

    public List<String> AuditMaven(File root) {
        return auditForCves(root, "audit-mvn");
    }
}
