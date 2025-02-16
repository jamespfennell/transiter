// Package sourceserver provides a client for the source server.
package sourceserver

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
)

type SourceServerClient struct {
	baseURL     string
	createdURLs []string
}

func NewSourceServerClient(baseURL string) *SourceServerClient {
	return &SourceServerClient{
		baseURL:     baseURL,
		createdURLs: []string{},
	}
}

func (c *SourceServerClient) Create(prefix, suffix string) (string, error) {
	resp, err := http.Post(c.baseURL, "application/json", nil)
	if err != nil {
		return "", fmt.Errorf("failed to create: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(body))
	}

	createdURLBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}
	createdURL := string(createdURLBytes) + suffix

	c.createdURLs = append(c.createdURLs, createdURL)

	return createdURL, nil
}

func (c *SourceServerClient) Put(url, content string) error {
	fullURL := c.baseURL + "/" + url
	req, err := http.NewRequest(http.MethodPut, fullURL, bytes.NewBufferString(content))
	if err != nil {
		return fmt.Errorf("failed to create PUT request: %w", err)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send PUT request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

func (c *SourceServerClient) Delete(url string) error {
	fullURL := c.baseURL + "/" + url
	req, err := http.NewRequest(http.MethodDelete, fullURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create DELETE request: %w", err)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send DELETE request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

func (c *SourceServerClient) Close() {
	for _, url := range c.createdURLs {
		_ = c.Delete(url)
	}
}
