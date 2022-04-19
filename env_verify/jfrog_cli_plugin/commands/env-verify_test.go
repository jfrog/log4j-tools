package commands

import (
	"github.com/jfrog/jfrog-cli-core/v2/utils/coreutils"
	"github.com/stretchr/testify/assert"
	"path/filepath"
	"regexp"
	"testing"
)

func TestHappyFlow(t *testing.T) {
	resourcesPath, err := coreutils.GetJfrogPluginsResourcesDir("env-verify")
	if nil != err {
		assert.Fail(t, "could not find plugin resources directory")
	}

	// Build the command line
	jarPath := filepath.Join(resourcesPath, "env-verify.jar")
	args := []string{"‐Dlog4j2.formatMsgNoLookups=True", "-jar", jarPath}
	err, out := getCmdOutput("java", args)
	assert.NoError(t, err)
	assert.NotRegexp(t, regexp.MustCompile(`log4j2\.formatMsgNoLookups.+NOT SET`), out)
}
