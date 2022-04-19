package commands

import (
	"github.com/jfrog/jfrog-cli-core/v2/utils/coreutils"
	"github.com/stretchr/testify/assert"
	"path/filepath"
	"runtime"
	"testing"
)

func TestHappyFlow(t *testing.T) {
	resourcesPath, err := coreutils.GetJfrogPluginsResourcesDir("scan-log4j-calls-jar")
	if nil != err {
		assert.Fail(t, "could not find plugin resources directory")
	}

	// Build the command line
	pyexeFilename := "scan-log4j-calls-jar"
	if runtime.GOOS == "windows" {
		pyexeFilename += ".exe"
	}
	pyexeFilepath := filepath.Join(resourcesPath, pyexeFilename)
	args := []string{"test_resources"}
	err, out := getCmdOutput(pyexeFilepath, args)
	assert.NoError(t, err)
	assert.Contains(t, out, "Vulnerable call")
}
