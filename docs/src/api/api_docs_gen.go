package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"text/template"

	gendoc "github.com/pseudomuto/protoc-gen-doc"
)

const (
	publicEndpointsFile = "public_endpoints.md"
	publicResourcesFile = "public_resources.md"
	adminFile           = "admin.md"
	inputFile           = "api_docs_gen_input.json"
	scriptDir           = "docs/src/api"
)

func main() {
	if err := run(); err != nil {
		panic(err)
	}
}

func run() error {
	b, err := os.ReadFile(filepath.Join(scriptDir, inputFile))
	if err != nil {
		return err
	}
	var in gendoc.Template
	if err := json.Unmarshal(b, &in); err != nil {
		return err
	}
	for _, file := range in.Files {
		switch file.Name {
		case "api/admin.proto":
			if err := generate(generateArgs{
				file:          file,
				scalars:       in.Scalars,
				template:      adminTmpl,
				outputFile:    adminFile,
				resourcesFile: adminFile,
				endpointsFile: adminFile,
			}); err != nil {
				return err
			}
		case "api/public.proto":
			if err := generate(generateArgs{
				file:          file,
				scalars:       in.Scalars,
				template:      publicResourcesTmpl,
				outputFile:    publicResourcesFile,
				resourcesFile: publicResourcesFile,
				endpointsFile: publicEndpointsFile,
			}); err != nil {
				return err
			}
			if err := generate(generateArgs{
				file:          file,
				scalars:       in.Scalars,
				template:      publicEndpointsTmpl,
				outputFile:    publicEndpointsFile,
				resourcesFile: publicResourcesFile,
				endpointsFile: publicEndpointsFile,
			}); err != nil {
				return err
			}
		default:
			return fmt.Errorf("unexpected proto file %q", file.Name)
		}
	}
	return nil
}

type generateArgs struct {
	file          *gendoc.File
	scalars       []*gendoc.ScalarValue
	template      string
	outputFile    string
	resourcesFile string
	endpointsFile string
}

func generate(args generateArgs) error {
	file := buildFile(args.file)

	scalerProtoTypes := map[string]bool{}
	for _, s := range args.scalars {
		scalerProtoTypes[s.ProtoType] = true
	}

	link := func(longName string) string {
		if scalerProtoTypes[longName] {
			return longName
		}
		var file string
		if isResponseLongName(longName) {
			file = args.endpointsFile
		} else {
			file = args.resourcesFile
		}
		return fmt.Sprintf("[%s](%s#%s)", longName, file, longName)
	}
	t := template.Must(template.New("base").Funcs(
		template.FuncMap{
			"link": link,
			"multiline": func(s string) string {
				s = gendoc.NoBrFilter(s)
				s = strings.Replace(s, "\n\n", "<br /><br />", -1)
				s = strings.Replace(s, "\n", " ", -1)
				return s
			},
		},
	).Parse(baseTmpl))
	t = template.Must(t.New("output").Parse(args.template))

	var b bytes.Buffer
	if err := t.Execute(&b, file); err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(scriptDir, args.outputFile), b.Bytes(), 0666); err != nil {
		return err
	}
	return nil
}

func buildFile(in *gendoc.File) *File {
	rootTypes := map[string]*Root{}
	var allTypes []Type
	for _, m := range in.Messages {
		allTypes = append(allTypes, Type{Message: m})
	}
	for _, e := range in.Enums {
		allTypes = append(allTypes, Type{Enum: e})
	}
	for _, t := range allTypes {
		rootTypeName := t.LongName()
		i := strings.Index(rootTypeName, ".")
		isRootType := i == -1
		if !isRootType {
			rootTypeName = rootTypeName[:i]
		}
		if _, ok := rootTypes[rootTypeName]; !ok {
			rootTypes[rootTypeName] = &Root{}
		}
		if isRootType {
			rootTypes[rootTypeName].Type = t
		} else {
			rootTypes[rootTypeName].Children = append(rootTypes[rootTypeName].Children, t)
		}
	}

	for _, r := range rootTypes {
		sort.Slice(r.Children, func(i, j int) bool {
			return r.Children[i].LongName() < r.Children[j].LongName()
		})
	}

	var endpoints []Endpoint
	for _, m := range in.Services[0].Methods {
		requestType := rootTypes[m.RequestFullType]
		delete(rootTypes, m.RequestFullType)
		responseType := rootTypes[m.ResponseFullType]
		if responseType.Type.IsResponseType() {
			delete(rootTypes, m.ResponseFullType)
		}
		endpoints = append(endpoints, Endpoint{
			Method:       m,
			RequestType:  *requestType,
			ResponseType: *responseType,
		})
	}

	var types []Root
	for _, r := range rootTypes {
		types = append(types, *r)
	}
	sort.Slice(types, func(i, j int) bool {
		return types[i].Type.LongName() < types[j].Type.LongName()
	})
	return &File{
		File:      in,
		Service:   in.Services[0],
		Endpoints: endpoints,
		Types:     types,
	}
}

type File struct {
	File      *gendoc.File
	Service   *gendoc.Service
	Endpoints []Endpoint
	// TODO: split into resources versus other
	Types []Root
}

type Endpoint struct {
	Method       *gendoc.ServiceMethod
	RequestType  Root
	ResponseType Root
}

type Root struct {
	Type     Type
	Children []Type
}

type Type struct {
	Message *gendoc.Message
	Enum    *gendoc.Enum
}

func (c Type) Name() string {
	if c.Message != nil {
		return c.Message.Name
	}
	return c.Enum.Name
}

func (c Type) LongName() string {
	if c.Message != nil {
		return c.Message.LongName
	}
	return c.Enum.LongName
}

func (c Type) Description() string {
	if c.Message != nil {
		return c.Message.Description
	}
	return c.Enum.Description
}

func (c Type) IsResponseType() bool {
	return isResponseLongName(c.LongName())
}

func isResponseLongName(longName string) bool {
	if i := strings.Index(longName, "."); i >= 0 {
		longName = longName[:i]
	}
	return strings.HasSuffix(longName, "Reply")
}

const baseTmpl = `
{{ define "type-doc" -}}
	{{.LongName}}

{{ .Description }}
	
{{ if .Message }}
{{ if .Message.HasFields }}
| Field | Type |  Description |
| ----- | ---- | ----------- |
{{range .Message.Fields -}}
  | {{.Name}} | {{ link .LongType}} | {{ multiline .Description }}
{{end}}
{{ else }}
No fields.
{{end}}
{{end}}

{{ if .Enum }}
| Name | Number | Description |
| ---- | ------ | ----------- |
{{range .Enum.Values -}}
  | {{.Name}} | {{.Number}} | {{.Description}} |
{{end}}
{{end}}
{{end}}

{{ define "root-doc" -}}
	{{- template "type-doc".Type -}}
		{{- if .Children -}}

		{{ range .Children }}
#### {{ template "type-doc" . }}
		{{- end -}}
	{{- end -}}
{{- end}}


{{ define "endpoints-doc" }}
{{range . -}}
## {{.Method.Description}}

### Request type: {{ template "root-doc" .RequestType }}

{{ if .ResponseType.Type.IsResponseType }}
### Response type: {{ template "root-doc" .ResponseType }}

{{ else }}
### Response type: {{ link .ResponseType.Type.LongName }}
{{ end }}
{{ end }}
{{end}}
`

const publicResourcesTmpl = `

# Public API resources

{{ .File.Description }}

{{ range .Types }}

## {{ template "root-doc" . }}

{{ end }}

## Other types

`

const publicEndpointsTmpl = `



# Public API endpoints

{{ template "endpoints-doc" .Endpoints }}

`

const adminTmpl = `


# {{ .File.Description }}

## Endpoints

{{ template "endpoints-doc" .Endpoints }}

## Types

{{ range .Types }}
### {{ template "root-doc" . }}
{{ end }}

`
