package commands

import (
	"github.com/stretchr/testify/assert"
	"path"
	"path/filepath"
	"testing"
)

func TestHappyFlow(t *testing.T) {
	// TODO - Add an API to get the resources directory
	resourcesPath := path.Join("..", "resources")

	// Build the command line
	jarPath := filepath.Join(resourcesPath, "scan_log4j_versions.jar")
	args := []string{"-jar", jarPath, "test_resources"}
	err, out := getCmdOutput("java", args)
	assert.NoError(t, err)
	assert.Contains(t, out, "vulnerable")
}
