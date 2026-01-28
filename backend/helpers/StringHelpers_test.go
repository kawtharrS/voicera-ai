package helpers

import "testing"

func TestIsEmpty(t *testing.T) {
	tests := []struct {
		input    string
		expected bool
	}{
		{"", true},
		{"hello", false},
		{" ", false},
	}

	for _, test := range tests {
		result := IsEmpty(test.input)
		if result != test.expected {
			t.Errorf("IsEmpty(%q) = %v; want %v", test.input, result, test.expected)
		}
	}
}

func TestLoadFileError(t *testing.T) {
	_, err := LoadFile("non_existent_file.txt")
	if err == nil {
		t.Error("expected error for non-existent file, got nil")
	}
}
