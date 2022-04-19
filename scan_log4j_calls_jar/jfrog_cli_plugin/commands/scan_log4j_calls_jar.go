package commands

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/jfrog/jfrog-cli-core/v2/plugins/components"
	"os/exec"
	"path/filepath"
	"runtime"
)

func GetCommand() components.Command {
	return components.Command{
		Name:        "run",
		Description: "Scan recursively for Java binary archive files",
		Arguments:   getArguments(),
		Flags:       getFlags(),
		Action: func(c *components.Context) error {
			return scanCmd(c)
		},
	}
}

func getArguments() []components.Argument {
	return []components.Argument{
		{
			Name:        "root-folder",
			Description: "Directory to start the recursive scan from",
		},
	}
}

func getFlags() []components.Flag {
	return []components.Flag{
		components.StringFlag{
			Name:         "class_regex",
			Description:  "Regular expression for required class name",
			DefaultValue: "",
			Mandatory:    false,
		},
		components.StringFlag{
			Name:         "method_regex",
			Description:  "Regular expression for required method name",
			DefaultValue: "",
			Mandatory:    false,
		},
		components.StringFlag{
			Name:         "quickmatch_string",
			Description:  "Static pre-condition string for file analysis",
			DefaultValue: "",
			Mandatory:    false,
		},
		components.StringFlag{
			Name:         "caller_block",
			Description:  "Regular expression for discarding caller classes",
			DefaultValue: "",
			Mandatory:    false,
		},
		components.BoolFlag{
			Name:         "class_existence",
			Description:  "When false, look for calls to class::method as specified by regexes. When true, --method_regex is ignored, and the tool will look for existence of classes specified by --class_regex in the jar.",
			DefaultValue: false,
		},
		components.BoolFlag{
			Name:         "no_quickmatch",
			Description:  "When true, the value of --quickmatch_string is ignored and all jar files are analyzed",
			DefaultValue: false,
		},
	}
}

func getCmdOutput(executable string, args []string) (error, string) {
	// Run the command
	cmd := exec.Command(executable, args...)
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		return err, ""
	}

	// Return the output and error value
	if stdout.Len() > 0 {
		return err, string(stdout.Bytes())
	}
	if stderr.Len() > 0 {
		// TODO
		return errors.New("command failed"), string(stderr.Bytes())
	}

	return err, ""
}

func appendStringArg(c *components.Context, optname string, args []string) []string {
	val := c.GetStringFlagValue(optname)
	if val != "" {
		args = append(args, "--"+optname, val)
	}
	return args
}

func appendBoolArg(c *components.Context, optname string, args []string) []string {
	if c.GetBoolFlagValue(optname) {
		args = append(args, "--"+optname)
	}
	return args
}

func scanCmd(c *components.Context) error {
	// Arg sanity
	if len(c.Arguments) != 1 {
		return errors.New("usage: jf scan_log4j_calls_jar run root-folder [--class_regex regex] [--method_regex regex] [--quickmatch_string quickmatch] [--caller_block regex] [--class_existence] [--no_quickmatch]")
	}

	// TODO - Add an API to get the resources directory
	resourcesPath := "resources"

	// Build the command line
	// TODO: Support different runtime.GOARCH ?
	pyexeFilename := "scan_log4j_calls_jar"
	if runtime.GOOS == "windows" {
		pyexeFilename += ".exe"
	}

	pyexeFilepath := filepath.Join(resourcesPath, pyexeFilename)
	args := []string{c.Arguments[0]}

	for _, optname := range [...]string{"class_regex", "method_regex", "quickmatch_string", "caller_block"} {
		args = appendStringArg(c, optname, args)
	}
	for _, optname := range [...]string{"class_existence", "no_quickmatch"} {
		args = appendBoolArg(c, optname, args)
	}

	// Run the command
	err, out := getCmdOutput(pyexeFilepath, args)
	if err != nil {
		// No need to print stderr for now
		return err
	}
	fmt.Println(out)
	return err
}
