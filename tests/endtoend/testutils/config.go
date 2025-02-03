package testutils

import (
	"bytes"
	"fmt"
	"html/template"
)

func CreateConfigFromTemplate(config string, data map[string]any) string {
	configTemplate := template.Must(template.New("config").Parse(config))
	configBuffer := bytes.Buffer{}
	err := configTemplate.Execute(&configBuffer, data)
	if err != nil {
		panic(fmt.Sprintf("failed to execute config template: %v", err))
	}
	return configBuffer.String()
}
