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
	jarPath := filepath.Join(resourcesPath, "scan_cve_2021_45046_config.jar")
	args := []string{"-jar", jarPath, "test_resources"}
	err, out := getCmdOutput("java", args)
	assert.NoError(t, err)
	assert.Contains(t, out, "Evidence:")
}
