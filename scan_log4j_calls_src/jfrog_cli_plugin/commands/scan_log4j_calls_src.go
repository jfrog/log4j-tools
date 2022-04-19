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
		Description: "Scan recursively for Java source files",
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
		return errors.New("no log4j2 logging calls were found"), string(stderr.Bytes())
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

func scanCmd(c *components.Context) error {
	// Arg sanity
	if len(c.Arguments) != 1 {
		return errors.New("usage: jf scan_log4j_calls_src run root-folder [--class_regex regex] [--method_regex regex]")
	}

	// TODO - Add an API to get the resources directory
	resourcesPath := "resources"

	// Build the command line
	// TODO: Support different runtime.GOARCH ?
	pyexeFilename := "scan_log4j_calls_src"
	if runtime.GOOS == "windows" {
		pyexeFilename += ".exe"
	}

	pyexeFilepath := filepath.Join(resourcesPath, pyexeFilename)
	args := []string{c.Arguments[0]}

	for _, optname := range [...]string{"class_regex", "method_regex"} {
		args = appendStringArg(c, optname, args)
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
