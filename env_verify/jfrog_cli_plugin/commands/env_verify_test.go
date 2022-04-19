package commands

import (
	"github.com/stretchr/testify/assert"
	"path"
	"path/filepath"
	"regexp"
	"testing"
)

func TestHappyFlow(t *testing.T) {
	// TODO - Add an API to get the resources directory
	resourcesPath := path.Join("..", "resources")

	// Build the command line
	jarPath := filepath.Join(resourcesPath, "env_verify.jar")
	args := []string{"‐Dlog4j2.formatMsgNoLookups=True", "-jar", jarPath}
	err, out := getCmdOutput("java", args)
	assert.NoError(t, err)
	assert.NotRegexp(t, regexp.MustCompile(`log4j2\.formatMsgNoLookups.+NOT SET`), out)
}
