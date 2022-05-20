package systems

import (
	"embed"
	"testing"

	"github.com/jamespfennell/transiter/config"
)

//go:embed *yaml
var yamlFiles embed.FS

func TestConfigsAreValid(t *testing.T) {
	files, err := yamlFiles.ReadDir(".")
	if err != nil {
		t.Fatalf("Failed to list config files: %s", err)
	}
	for _, file := range files {
		content, err := yamlFiles.ReadFile(file.Name())
		if err != nil {
			t.Errorf("Failed to read %s: %s", file.Name(), err)
		}
		_, err = config.UnmarshalFromYaml(content)
		if err != nil {
			t.Errorf("Failed to parse %s as a yaml system config: %s", file.Name(), err)
		}
	}
}
