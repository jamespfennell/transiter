package table

import "testing"

const expected = `┌───────┬───────┬───────┐
│ Hello │ World │ Again │
├───────┼───────┼───────┤
│ A     │ B     │ C     │
│ D     │       │       │
└───────┴───────┴───────┘
`

func TestTable(t *testing.T) {
	table := New()
	table.AddRow("Hello", "World", "Again")
	table.AddSeperator()
	table.AddRow("A", "B", "C")
	table.AddRow("D")

	s := table.Render()
	if s != expected {
		t.Errorf("table not correct\nactual:\n%sexpected:\n%s", s, expected)
	}
}
