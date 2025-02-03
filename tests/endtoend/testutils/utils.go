// Package testutils provides utilities for testing.
package testutils

import (
	"fmt"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func AssertEqual(t *testing.T, got, want any) {
	if diff := cmp.Diff(got, want); diff != "" {
		t.Errorf("got %+v, want %+v\n%s", got, want, diff)
	}
}

func AssertHTTPErrorCode(t *testing.T, err error, code int) {
	if err == nil {
		t.Errorf("expected error with status code %d, got nil", code)
	}
	expectedErrorText := fmt.Sprintf("HTTP request failed with status %d", code)
	if !strings.Contains(err.Error(), expectedErrorText) {
		t.Errorf("expected error with status code %d, got %v", code, err)
	}
}

func Ptr[T any](v T) *T {
	return &v
}
