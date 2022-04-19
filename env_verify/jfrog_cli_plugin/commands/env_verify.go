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
		Description: "Alert on JVM-based mitigations to Log4Shell",
		Arguments:   getArguments(),
		Action: func(c *components.Context) error {
			return verifyCmd(c)
		},
	}
}

func getArguments() []components.Argument {
	return []components.Argument{
		{
			Name:        "VM_ARGS",
			Description: "Arguments to the JVM, as passed to the original Java program",
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

func verifyCmd(c *components.Context) error {
	// Check that "java" is on the path
	if which.Which("java") == "" && which.Which("java.exe") == "" {
		return errors.New("could not find \"java\" executable in PATH")
	}

	// TODO - Add an API to get the resources directory
	resourcesPath := "resources"

	// // Take all arguments as VMARGS, just add "-D" prefix
	args := c.Arguments
	for i, arg := range args {
		args[i] = "-D" + arg
	}
	jarPath := filepath.Join(resourcesPath, "env_verify.jar")
	args = append(args, "-jar", jarPath)

	// Run the command
	err, out := getCmdOutput("java", args)
	if err != nil {
		// No need to print stderr for now
		return err
	}
	fmt.Println(out)
	return err
}
