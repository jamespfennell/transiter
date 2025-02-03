package testutils

import (
	"archive/zip"
	"bytes"
	"fmt"
	"strings"
)

type ZipBuilder struct {
	files map[string]string
}

func NewZipBuilder() *ZipBuilder {
	return &ZipBuilder{
		files: make(map[string]string),
	}
}

func (b *ZipBuilder) AddOrReplaceFile(name string, lines ...string) *ZipBuilder {
	b.files[name] = strings.Join(lines, "\n")
	return b
}

func (b *ZipBuilder) Build() (*string, error) {
	return toZip(b.files)
}

func (b *ZipBuilder) MustBuild() string {
	result, err := b.Build()
	if err != nil {
		panic(fmt.Sprintf("failed to build txtar: %v", err))
	}
	return *result
}

func toZip(files map[string]string) (*string, error) {
	// Create a buffer to hold the zip archive
	var outputBuffer bytes.Buffer
	zipWriter := zip.NewWriter(&outputBuffer)

	// Add files to the zip archive
	for fileName, content := range files {
		writer, err := zipWriter.Create(fileName)
		if err != nil {
			return nil, fmt.Errorf("failed to create file in zip: %w", err)
		}
		_, err = writer.Write([]byte(content))
		if err != nil {
			return nil, fmt.Errorf("failed to write file content to zip: %w", err)
		}
	}

	// Close the zip writer
	err := zipWriter.Close()
	if err != nil {
		return nil, fmt.Errorf("failed to finalize zip archive: %w", err)
	}

	result := outputBuffer.String()
	return &result, nil
}
