// Package version contains the Transiter version and related information
package version

import (
	_ "embed"
	"fmt"
	"strings"
)

//go:embed BASE_VERSION
var baseVersion string

var version string

func Version() string {
	if version == "" {
		return fmt.Sprintf("%s-alpha+dev", strings.TrimSpace(baseVersion))
	}
	return version
}
