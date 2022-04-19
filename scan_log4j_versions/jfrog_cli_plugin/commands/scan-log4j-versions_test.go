package commands

import (
	"github.com/stretchr/testify/assert"
	"path/filepath"
	"github.com/jfrog/jfrog-cli-core/v2/utils/coreutils"
	"testing"
)

func TestHappyFlow(t *testing.T) {
	resourcesPath, err := coreutils.GetJfrogPluginsResourcesDir("scan-log4j-versions")
	if nil != err {
		assert.Fail(t, "could not find plugin resources directory")
	}

	// Build the command line
	jarPath := filepath.Join(resourcesPath, "scan-log4j-versions.jar")
	args := []string{"-jar", jarPath, "test_resources"}
	err, out := getCmdOutput("java", args)
	assert.NoError(t, err)
	assert.Contains(t, out, "vulnerable")
}
