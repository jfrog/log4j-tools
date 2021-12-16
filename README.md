# log4j-tools

### Quick links

Click to find:

| [Inclusions of `log4j2` in compiled code](#scan_jndimanager_versionspy) | [Calls to `log4j2` in compiled code](#scan_log4j_calls_jarpy) | [Calls to `log4j2` in source code](#scan_log4j_calls_srcpy) |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------- |

### Overview

CVE-2021-44228 poses a serious threat to a wide range of Java-based applications. The important questions a developer may ask in this context are:

### 1. Does my code include `log4j2`?

Does the released code include `log4j2`? Which version of the library is included there? Answering these questions may not be immediate due to two factors:

1) Transitive dependencies: while `log4j2` may not be in the direct dependency list of the project, it may be used indirectly by some other dependency.

2) The code of this library may not appear directly as a separate file (i.e., `log4j2-core-2.xx.0.jar`), but rather be bundled in some other code jar file.

JFrog is releasing a tool to help resolve this problem: [`scan_jndimanager_versions`](#scan_jndimanager_versionspy). The tool looks for the **class code** of `JndiManager` **(regardless of containing `.jar` file names and content of `pom.xml` files)**, which is required for the vulnerability to be exploitable, and checks whether its version is fixed one (i.e., 2.15 or above) by testing for existence of an indicative string. Both Python and Java implementations are included.

### 2. Where does my code use `log4j2`? 

The question is relevant for the cases where the developer would like to verify if the calls to log4j2 in the codebase may pass potentially attacker-controlled data. While the safest way to fix the vulnerability, as discussed in the advisories, is to apply the appropriate patches and global flags, controlling for and verifying the potential impact under assumption of unpatched `log4j2` may be valuable in many situations. In order to address this problem JFrog is releasing two scripts:

1. [`scan_log4j2_calls_src.py`](#scan_log4j_calls_srcpy), which locates calls to log4j2 logging functions (info, log, error etc.) with non-constant arguments in *.java source files* and reports the findings on the level of source file and line
2. [`scan_log4j2_calls_jar.py`](#scan_log4j_calls_jarpy), which locates the calls to logging functions in *compiled .jar*s, and reports the findings as class name and method names in which each call appears.

## Usage instructions

### `scan_jndimanager_versions.py`

The tool requires python3, without additional dependencies.

##### Usage

```
python scan_jndimanager_versions.py root-folder
```

The tool will scan `root_folder` recursively for `.jar` and `.war` files; in each located file the tool looks for a `*log4j/core/net/JndiManager.class` code (recursively in each `.jar` file). If the code is located, and does not contain `allowedJndiProtocols`  string constant (added in 2.15), the file as reported as containing a vulnerable implementation if `JndiManager`. 

------

### `scan_jndimanager_versions.jar`

The tool requires java runtime, without additional dependencies. It can be [recompiled](#compiling-scan_jndimanager_versionsjar-from-source) from the provided source.

##### Usage

```
java -jar scan_jndimanager_versions.jar root-folder
```

The tool will scan `root_folder` recursively for `.jar` and `.war` files; in each located file the tool looks for a `*log4j/core/net/JndiManager.class` code. If the code is located, and does not contain `allowedJndiProtocols`  string constant (added in 2.15), the file as reported as containing a vulnerable implementation if `JndiManager`. 

------

### `scan_log4j_calls_jar.py`

The tool requires python 3 and the following 3rd party libraries: `jawa`, `tqdm`, `easyargs`, `colorama`

##### Dependencies installation

```
pip install -r requirements.txt
```

##### Usage

The default use case:

```
python scan_log4j_calls_jar.py root-folder
```

will recursively scan all `.jar` files in `root-folder`, for each printing out locations (class name and method name) of calls to `info`/`warn`/`error`/`log`/`debug` /`trace`/`fatal` methods of `log4j2.Logger`. 

The tool may be configured for additional use cases using the following command line flags.

| Flag                  | Default value                                                | Use                                                          |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `--class_regex`       | org/apache/logging/log4j/Logger                              | Regular expression for required class name                   |
| `--method_regex`      | (info&#124;warn&#124;error&#124;log&#124;debug&#124;trace&#124;fatal) | Regular expression for required method name                  |
| `--quickmatch_string` | log4j                                                        | Pre-condition for file analysis: .jar files not containing the specified string will be ignored |
| `--class_existence`   | Not set                                                      | When not set, look for calls to class::method as  specified by regexes. When set, `--method_regex` is ignored, and the tool will look for *existence* of classes specified by `--class_regex` in the jar. |
| `--no_quickmatch`     | Not set                                                      | When set, the value of `--quickmatch_string` is ignored and all jar files are analyzed |

For example, 

```
python scan_log4j_calls_jar.py --class_regex ".*JndiManager$" --class_existence --no_quickmatch root-folder
```

Will scan all `.jar` files (even if they do have no mentions of `log4j2`) for the existence of a class ending with `JndiManager`. 

------

### `scan_log4j_calls_src.py`
The tool requires python 3 and the following 3rd party libraries: `javalang`, `tqdm`, `easyargs`, `colorama`

##### Dependencies installation

```
pip install -r requirements.txt
```

##### Usage

The default use case:

```
python scan_log4j_calls_src.py root-folder
```

will recursively scan all `.java` files in `root-folder`, for each printing out the locations (file name and corresponding code lines) of calls to `log4j2` logging methods.

The tool may be configured for additional use cases using the following command line flags:

| Flag             | Default value                                                | Use                                         |
| ---------------- | ------------------------------------------------------------ | ------------------------------------------- |
| `--class_regex`  | org/apache/logging/log4j/Logger                              | Regular expression for required class name  |
| `--method_regex` | (info&#124;warn&#124;error&#124;log&#124;debug&#124;trace&#124;fatal) | Regular expression for required method name |

### Compiling `scan_jndimanager_versions.jar` from source

```
cd scan_jndimanager_versions
gradle build
cp build/libs/scan_jndimanager_versions.jar ..
```

