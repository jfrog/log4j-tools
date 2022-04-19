package main

import (
	"github.com/jfrog/jfrog-cli-core/v2/plugins"
	"github.com/jfrog/jfrog-cli-core/v2/plugins/components"
	"scan-cve-2021-45046-config/commands"
)

func main() {
	plugins.PluginMain(getApp())
}

func getApp() components.App {
	app := components.App{}
	app.Name = "scan-cve-2021-45046-config"
	app.Description = "The tool will scan recursively for Log4j configurations applicable to CVE-2021-45046"
	app.Version = "v1.0.1"
	app.Commands = getCommands()
	return app
}

func getCommands() []components.Command {
	return []components.Command{
		commands.GetCommand()}
}
