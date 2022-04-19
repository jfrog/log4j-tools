package log4shell_xray_wrapper;

import picocli.CommandLine;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.stream.Collectors;

@CommandLine.Command(
        name = "log4shell_xray_wrapper",
        version = "log4shell_xray_wrapper 1.0",
        mixinStandardHelpOptions = true)
public class Main implements Callable<Integer> {
    private JFrogCLI jFrogCLI;
    private boolean hasGradle;
    private boolean hasMaven;

    private static final Set<String> relevantCves =
            Set.of("CVE-2021-44228", "CVE-2021-45046", "CVE-2021-45105");

    @CommandLine.Parameters(paramLabel = "<rootDir>")
    private File rootDir;

    @CommandLine.Option(names = {"-r", "--recurse"})
    private boolean recurse = false;

    @CommandLine.Option(names = {"-v", "--verbose"})
    private boolean verbose = false;

    private class NotAProject extends Exception {
        File rootDir;

        public NotAProject(File rootDir) {
            super();
            this.rootDir = rootDir;
        }
    }

    private class MissingProjectTool extends Exception {
        ProjectType projectType;

        public MissingProjectTool(ProjectType projectType) {
            super("Missing project tool for " + projectType.toString() + ".");
            this.projectType = projectType;
        }
    }

    private enum ProjectType {
        MAVEN {
            public String toString() {
                return "Maven";
            }
        },
        GRADLE {
            public String toString() {
                return "Gradle";
            }
        },
    }

    private static final Map<String, ProjectType> projectMap =
            Map.of(
                    "pom.xml", ProjectType.MAVEN,
                    "build.gradle", ProjectType.GRADLE);

    private boolean tryRun(String command) {
        boolean isWindows = System.getProperty("os.name").toLowerCase().startsWith("windows");
        try {
            if (isWindows) {
                Runtime.getRuntime().exec("cmd /c " + command);
            } else {
                Runtime.getRuntime().exec(command);
            }
            return true;
        } catch (IOException e) {
            return false;
        }
    }

    private ProjectType getProjectType(File rootDir) throws NotAProject {
        for (Map.Entry<String, ProjectType> entry : projectMap.entrySet()) {
            if (new File(rootDir, entry.getKey()).isFile()) {
                return entry.getValue();
            }
        }
        throw new NotAProject(rootDir);
    }

    private void ensureProjectPrerequisites(ProjectType projectType) throws MissingProjectTool {

        boolean toolFound = false;
        switch (projectType) {
            case GRADLE:
                if (hasGradle) {
                    return;
                }
                toolFound = tryRun("gradle --version");
                hasGradle = toolFound;
                break;
            case MAVEN:
                if (hasMaven) {
                    return;
                }
                toolFound = tryRun("mvn --version");
                hasMaven = toolFound;
                break;
        }
        if (!toolFound) {
            throw new MissingProjectTool(projectType);
        }
    }

    private int Check() {
        try {
            jFrogCLI = new JFrogCLI(verbose);
            if (recurse) {
                checkRecursive(rootDir);
            } else {
                for (String cve : checkDirectory(rootDir).cves) {
                    System.out.println("Xray detected " + cve);
                }
            }
            return 0;
        } catch (JFrogCLI.Missing ignored) {
            System.err.println("ERROR: JFrog CLI must be available");
        } catch (JFrogCLI.WrongVersion e) {
            System.err.println(
                    "ERROR: JFrog CLI version must be 2.6.2 or later. Found "
                            + e.version.toString());
        } catch (NotAProject e) {
            System.err.println(
                    "ERROR: No Maven (pom.xml) or Gradle (build.gradle) projects found at "
                            + e.rootDir.toString());
        } catch (MissingProjectTool e) {
            System.err.println(
                    "ERROR: "
                            + e.projectType.toString()
                            + " must be installed to analyze a "
                            + e.projectType.toString()
                            + " project.");
        } catch (JFrogCLI.NoDefaultServer e) {
            System.err.println("ERROR: JFrog CLI default server has no Xray URL configured");
            System.err.println(
                    "Visit https://www.jfrog.com/confluence/display/CLI/JFrog+CLI#JFrogCLI-AddingandEditingConfiguredServers for more details");
        } catch (IOException e) {
            e.printStackTrace();
        }
        return -1;
    }

    private List<String> filterCves(List<String> cves) {
        return cves.stream().filter(relevantCves::contains).collect(Collectors.toList());
    }

    private class CheckResult {
        File rootDir;
        List<String> cves;

        public CheckResult(File rootDir, List<String> cves) {
            this.rootDir = rootDir;
            this.cves = filterCves(cves);
        }
    }

    private void checkRecursive(File rootDir) throws IOException {
        if (Files.walk(rootDir.toPath())
                .filter(this::isProjectDirectory)
                        .findAny().isEmpty()) {
            System.err.println("WARNING: " + rootDir + " tree does not contain a supported project");
            return;
        }
        Files.walk(rootDir.toPath())
                .filter(this::isProjectDirectory)
                .map(
                        root -> {
                            try {
                                return checkDirectory(root.toFile());
                            } catch (MissingProjectTool e) {
                                System.err.println(
                                        "WARNING: "
                                                + e.projectType.toString()
                                                + " must be installed to analyze "
                                                + e.projectType.toString()
                                                + " project.");
                                System.err.println("SKIPPING: " + root);
                                return null;
                            } catch (NotAProject e) {
                                return null;
                            }
                        })
                .filter(Objects::nonNull)
                .forEach(
                        checkResult -> {
                            for (String cve : checkResult.cves) {
                                System.out.println("    Xray detected " + cve);
                            }
                        });
    }

    private boolean isProjectDirectory(Path rootDir) {
        try {
            getProjectType(rootDir.toFile());
            return true;
        } catch (NotAProject e) {
            return false;
        }
    }

    private CheckResult checkDirectory(File rootDir) throws MissingProjectTool, NotAProject {
        ProjectType projectType = getProjectType(rootDir);

        ensureProjectPrerequisites(projectType);

        List<String> cves = List.of();
        switch (projectType) {
            case GRADLE:
                System.out.println("Handling " + projectType +" project at " + rootDir + "...");
                cves = jFrogCLI.AuditGradle(rootDir);
                break;
            case MAVEN:
                System.out.println("Handling " + projectType +" project at " + rootDir + "...");
                cves = jFrogCLI.AuditMaven(rootDir);
                break;
        }
        return new CheckResult(rootDir, cves);
    }

    @Override
    public Integer call() {
        return Check();
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new Main()).execute(args);
        System.exit(exitCode);
    }
}
