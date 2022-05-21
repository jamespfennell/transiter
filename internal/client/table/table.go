// Package table contains a utility for printing tables on the command line.
package table

import (
	"fmt"
	"strings"
)

type Table struct {
	rows []row
}

func New() *Table {
	return &Table{}
}

func (t *Table) AddRow(cells ...string) {
	t.rows = append(t.rows, row{data: cells})
}

func (t *Table) AddSeperator() {
	t.rows = append(t.rows, row{isSeperator: true})
}

func (t *Table) Render() string {
	var widths []int
	for _, row := range t.rows {
		if row.isSeperator {
			continue
		}
		for i, cell := range row.data {
			if len(widths) == i {
				widths = append(widths, 0)
			}
			if widths[i] < len(cell) {
				widths[i] = len(cell)
			}
		}
	}
	var b strings.Builder
	writeSeparator(&b, widths, "┌", "┬", "┐")
	for _, row := range t.rows {
		if row.isSeperator {
			writeSeparator(&b, widths, "├", "┼", "┤")
			continue
		}
		for i, width := range widths {
			cell := ""
			if i < len(row.data) {
				cell = row.data[i]
			}
			fmt.Fprintf(&b, "│ %-*s ", width, cell)

		}
		b.WriteString("│\n")
	}
	writeSeparator(&b, widths, "└", "┴", "┘")
	return b.String()
}

func writeSeparator(b *strings.Builder, widths []int, l, c, r string) {
	b.WriteString(l)
	b.WriteString("─")
	for i, width := range widths {
		if i != 0 {
			b.WriteString("─")
			b.WriteString(c)
			b.WriteString("─")
		}
		b.WriteString(strings.Repeat("─", width))
	}
	b.WriteString("─")
	b.WriteString(r)
	b.WriteString("\n")
}

type row struct {
	isSeperator bool
	data        []string
}
