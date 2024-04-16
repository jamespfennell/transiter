// Package types contains Go types corresponding to database types
package types

import (
	"database/sql/driver"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"math"
)

type GeographyType uint32

const (
	Point GeographyType = 0x20000001
)

type Geography struct {
	Valid     bool
	Type      GeographyType
	Longitude float64
	Latitude  float64
}

func NewPoint(longitude float64, latitude float64) Geography {
	return Geography{
		Valid:     true,
		Type:      Point,
		Longitude: longitude,
		Latitude:  latitude,
	}
}

func (g *Geography) NullableLongitude() *float64 {
	if !g.Valid {
		return nil
	}
	return &g.Longitude
}

func (g *Geography) NullableLatitude() *float64 {
	if !g.Valid {
		return nil
	}
	return &g.Latitude
}

func (g *Geography) Scan(src any) error {
	if src == nil {
		return nil
	}
	g.Valid = true
	b, err := hex.DecodeString(src.(string))
	if err != nil {
		return err
	}

	var byteOrder binary.ByteOrder
	switch b[0] {
	case 0:
		byteOrder = binary.BigEndian
	case 1:
		byteOrder = binary.LittleEndian
	default:
		return fmt.Errorf("invalid byte order 0x%02x, require 0x00 (big endian) or 0x01 (little endian)", b[0])
	}

	geographyType := GeographyType(byteOrder.Uint32(b[1:5]))
	switch geographyType {
	case Point:
		g.Type = Point
		g.Longitude = math.Float64frombits(byteOrder.Uint64(b[9:17]))
		g.Latitude = math.Float64frombits(byteOrder.Uint64(b[17:25]))
		return nil
	default:
		return fmt.Errorf("unsupported PostGIS type code 0x%x", geographyType)
	}
}

func (g Geography) Value() (driver.Value, error) {
	if !g.Valid {
		return nil, nil
	}
	b := make([]byte, 25)
	b[0] = 1
	binary.LittleEndian.PutUint32(b[1:5], uint32(Point))
	binary.LittleEndian.PutUint32(b[5:9], uint32(4326))
	binary.LittleEndian.PutUint64(b[9:17], math.Float64bits(g.Longitude))
	binary.LittleEndian.PutUint64(b[17:25], math.Float64bits(g.Latitude))
	// return b, nil
	return hex.EncodeToString(b), nil
}
