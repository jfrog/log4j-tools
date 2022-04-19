package commands

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/hairyhenderson/go-which"
	"github.com/jfrog/jfrog-cli-core/v2/plugins/components"
	"os/exec"
	"path/filepath"
)

func GetCommand() components.Command {
	return components.Command{
		Name:        "run",
		Description: "Scan recursively for Log4j configuration files",
		Arguments:   getArguments(),
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
	// Check that "java" is on the path
	if which.Which("java") == "" && which.Which("java.exe") == "" {
		return errors.New("could not find \"java\" executable in PATH")
	}

	// Arg sanity
	if len(c.Arguments) != 1 {
		return errors.New("usage: jf scan_cve_2021_45046_config run root-folder")
	}

	// TODO - Add an API to get the resources directory
	resourcesPath := "resources"

	// Build the command line
	jarPath := filepath.Join(resourcesPath, "scan_cve_2021_45046_config.jar")
	args := []string{"-jar", jarPath}
	rootdir := c.Arguments[0]
	args = append(args, rootdir)


	// Run the command
	err, out := getCmdOutput("java", args)
	if err != nil {
		// No need to print stderr for now
		return err
	}
	fmt.Println(out)
	return err
}
