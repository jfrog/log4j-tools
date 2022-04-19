package commands

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/hairyhenderson/go-which"
	"github.com/jfrog/jfrog-cli-core/v2/plugins/components"
	"github.com/jfrog/jfrog-cli-core/v2/utils/coreutils"
	"os/exec"
	"path/filepath"
)

func GetCommand() components.Command {
	return components.Command{
		Name:        "run",
		Description: "Scan recursively for compiled Java files",
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
			Name:         "exclude",
			Description:  "Don't scan the specified directories",
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
		return errors.New("command failed"), string(stderr.Bytes())
	}

	return err, ""
}

func scanCmd(c *components.Context) error {
	// Arg sanity
	if len(c.Arguments) != 1 {
		return errors.New("usage: jf scan-log4j-versions run root-folder [--exclude folder1 folder2 ..]")
	}

	// Check that "java" is on the path
	if which.Which("java") == "" && which.Which("java.exe") == "" {
		return errors.New("could not find \"java\" executable in PATH")
	}

	resourcesPath, err := coreutils.GetJfrogPluginsResourcesDir("scan-log4j-versions")
	if nil != err {
		return errors.New("could not find plugin resources directory")
	}

	// Build the command line
	jarPath := filepath.Join(resourcesPath, "scan-log4j-versions.jar")
	args := []string{"-jar", jarPath}
	rootdir := c.Arguments[0]
	args = append(args, rootdir)

	excludeDir := c.GetStringFlagValue("exclude")
	if excludeDir != "" {
		args = append(args, "-exclude", excludeDir)
	}

	// Run the command
	err, out := getCmdOutput("java", args)
	if err != nil {
		// No need to print stderr for now
		return err
	}
	fmt.Println(out)
	return err
}
