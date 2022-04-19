# scan-log4j-calls-jar

## About this plugin
This plugin recursively scans all `.jar` files in `root-folder`, for each printing out locations (class name and method name) of calls to `info`/`warn`/`error`/`log`/`debug` /`trace`/`fatal` methods of `log4j2.Logger`.

The plugin can be configured for additional use cases using command line flags.

Typical output looks like this:

<img src="img/scan_log4j_jar.PNG" />



## Usage example

![Usage example](img/scan-log4j-calls-jar.gif)



## Installation with JFrog CLI

Installing the latest version:

`$ jf plugin install scan-log4j-calls-jar`

Installing a specific version:

`$ jf plugin install scan-log4j-calls-jar@version`

Uninstalling a plugin:

`$ jf plugin uninstall scan-log4j-calls-jar`

## Usage
### Commands
`jf scan-log4j-calls-jar run root-folder [--class_regex regex] [--method_regex regex] [--quickmatch_string quickmatch] [--caller_block regex] [--class_existence] [--no_quickmatch]`

* run

  - Arguments:
      - root-folder - Directory to start the recursive scan from
  - Flags:
      - class_regex - Regular expression for required class name **[Default: `org/apache/logging/log4j/Logger`]**
      - method_regex - Regular expression for required method name **[Default: `(info|warn|error|log|debug|trace|fatal|catching|throwing|traceEntry|printf|logMessage)`]**
      - quickmatch_string - Pre-condition for file analysis: .jar files not containing the specified string will be ignored **[Default: log4j]**
      - caller_block - If caller class matches this regex, it will *not* be displayed **[Default: `.*org/apache/logging`]**
      - class_existence - When not set, look for calls to class::method as  specified by regexes. When set, `--method_regex` is ignored, and the tool will look for *existence* of classes specified by `--class_regex` in the jar. **[Default: false]**
      - no_quickmatch - When set, the value of `--quickmatch_string` is ignored and all jar files are analyzed **[Default: false]**
  - Example:
  ```
  $ jf scan-log4j-calls-jar run --class_regex ".*JndiManager$" --class_existence --no_quickmatch root-folder
  ```



## Additional info
None.

## Release Notes
The release notes are available [here](RELEASE.md).
