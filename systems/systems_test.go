package systems

import (
	"embed"
	"testing"

	"github.com/ghodss/yaml"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"google.golang.org/protobuf/encoding/protojson"
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
		_, err = unmarshalFromYaml(content)
		if err != nil {
			t.Errorf("Failed to parse %s as a yaml system config: %s", file.Name(), err)
		}
	}
}

func unmarshalFromYaml(y []byte) (*api.SystemConfig, error) {
	j, err := yaml.YAMLToJSON(y)
	if err != nil {
		return nil, err
	}
	var config api.SystemConfig
	if err := protojson.Unmarshal(j, &config); err != nil {
		return nil, err
	}
	return &config, nil
}
