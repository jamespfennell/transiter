// Package argsflag defines a flag that can accept template arguments.
package argsflag

import (
	"flag"
	"fmt"
	"strings"
)

// Flag implements the standard library's Value and Getter interfaces.
type Flag struct {
	Values     map[string]string
	hasBeenSet bool
}

func (f *Flag) String() string {
	return "todo"
}

func (f *Flag) Set(rawValue string) error {
	s := strings.SplitN(rawValue, "=", 2)
	if len(s) != 2 {
		return fmt.Errorf("raw args value %q is not of the form key=value", rawValue)
	}
	key := s[0]
	value := s[1]
	if _, alreadySet := f.Values[key]; alreadySet {
		return fmt.Errorf("args key %q already set (to %q)", key, value)
	}
	f.Values[key] = value
	f.hasBeenSet = true
	return nil
}

func (f *Flag) Get() interface{} {
	return f.Values
}

// CliFlag implements the Cli package's Flag interface.
type CliFlag struct {
	Name  string
	Usage string
	flag  Flag
}

func NewCliFlag(Name, Usage string, Values map[string]string) *CliFlag {
	return &CliFlag{
		Name:  Name,
		Usage: Usage,
		flag: Flag{
			Values: Values,
		},
	}
}

func (c *CliFlag) String() string {
	return c.flag.String()
}

func (c *CliFlag) Apply(f *flag.FlagSet) error {
	f.Var(&c.flag, c.Name, c.Usage)
	return nil
}

func (c *CliFlag) Names() []string {
	return []string{c.Name}
}

func (c *CliFlag) IsSet() bool {
	return c.flag.hasBeenSet
}
