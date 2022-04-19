package commands

import (
	"github.com/stretchr/testify/assert"
	"path"
	"path/filepath"
	"runtime"
	"testing"
)

func TestHappyFlow(t *testing.T) {
	// TODO - Add an API to get the resources directory
	resourcesPath := path.Join("..", "resources")

	// Build the command line
	pyexeFilename := "scan_log4j_calls_src"
	if runtime.GOOS == "windows" {
		pyexeFilename += ".exe"
	}
	pyexeFilepath := filepath.Join(resourcesPath, pyexeFilename)
	args := []string{"test_resources"}
	err, out := getCmdOutput(pyexeFilepath, args)
	assert.NoError(t, err)
	assert.Contains(t, out, ".java")
}
