// Package config contains the definition of the system config Yaml format used by Transiter
package config

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"gopkg.in/yaml.v3"
)

type SystemConfig struct {
	Name  string
	Feeds []FeedConfig
}

type FeedConfig struct {
	Id string

	AutoUpdateEnabled bool           `yaml:"autoUpdateEnabled"`
	AutoUpdatePeriod  *time.Duration `yaml:"autoUpdatePeriod"`

	Url         string
	HttpTimeout *time.Duration    `yaml:"httpTimeout"`
	HttpHeaders map[string]string `yaml:"httpHeaders"`

	Parser              Parser
	GtfsStaticOptions   GtfsStaticOptions   `yaml:"gtfsStaticOptions"`
	GtfsRealtimeOptions GtfsRealtimeOptions `yaml:"gtfsRealtimeOptions"`
}

type Parser string

const (
	GtfsStatic     Parser = "GTFS_STATIC"
	GtfsRealtime   Parser = "GTFS_REALTIME"
	DirectionRules Parser = "DIRECTION_RULES"
)

type TransfersStrategy string

const (
	Default       TransfersStrategy = "DEFAULT"
	GroupStations TransfersStrategy = "GROUP_STATIONS"
)

type GtfsStaticOptions struct {
	TransfersStrategy   TransfersStrategy
	TransfersExceptions []TransfersException
}

type TransfersException struct {
	StopId1  string
	StopId2  string
	Strategy TransfersStrategy
}

type GtfsRealtimeExtension string

const (
	UsNySubwayTrips  GtfsRealtimeExtension = "US_NY_SUBWAY_TRIPS"
	UsNySubwayAlerts GtfsRealtimeExtension = "US_NY_SUBWAY_ALERTS"
)

type GtfsRealtimeOptions struct {
	Extensions []GtfsRealtimeExtension
}

func ConvertApiSystemConfig(sc *api.SystemConfig) *SystemConfig {
	result := &SystemConfig{
		Name: sc.Name,
	}
	for _, feed := range sc.Feeds {
		result.Feeds = append(result.Feeds, *ConvertApiFeedConfig(feed))
	}
	return result
}

func ConvertApiFeedConfig(fc *api.FeedConfig) *FeedConfig {
	result := &FeedConfig{
		Url:         fc.Url,
		HttpHeaders: fc.HttpHeaders,
	}
	if fc.HttpTimeout != nil {
		timeout := time.Millisecond * time.Duration(*fc.HttpTimeout)
		result.HttpTimeout = &timeout
	}

	switch parser := fc.Parser.(type) {
	case *api.FeedConfig_GtfsStaticParser_:
		var internalExceptions []TransfersException
		for _, exception := range parser.GtfsStaticParser.TransfersExceptions {
			internalExceptions = append(internalExceptions, TransfersException{
				StopId1:  exception.StopId_1,
				StopId2:  exception.StopId_2,
				Strategy: convertApiTransfersStrategy(exception.Strategy),
			})
		}
		result.Parser = GtfsStatic
		result.GtfsStaticOptions = GtfsStaticOptions{
			TransfersStrategy:   convertApiTransfersStrategy(parser.GtfsStaticParser.TransfersStrategy),
			TransfersExceptions: internalExceptions,
		}
	case *api.FeedConfig_GtfsRealtimeParser_:
		var internalExts []GtfsRealtimeExtension
		for _, ext := range parser.GtfsRealtimeParser.Extensions {
			switch ext {
			case api.GtfsRealtimeExtension_US_NY_SUBWAY_ALERTS:
				internalExts = append(internalExts, UsNySubwayAlerts)
			case api.GtfsRealtimeExtension_US_NY_SUBWAY_TRIPS:
				internalExts = append(internalExts, UsNySubwayTrips)
			}
		}
		result.Parser = GtfsRealtime
		result.GtfsRealtimeOptions = GtfsRealtimeOptions{
			Extensions: internalExts,
		}
	case *api.FeedConfig_DirectionRulesParser_:
		result.Parser = DirectionRules
	}
	return result
}

func convertApiTransfersStrategy(s api.FeedConfig_GtfsStaticParser_TransfersStrategy) TransfersStrategy {
	switch s {
	case api.FeedConfig_GtfsStaticParser_DEFAULT:
		return Default
	case api.FeedConfig_GtfsStaticParser_GROUP_STATIONS:
		return GroupStations
	}
	return Default
}

func ConvertSystemConfig(sc *SystemConfig) *api.SystemConfig {
	result := &api.SystemConfig{
		Name: sc.Name,
	}
	for _, feed := range sc.Feeds {
		result.Feeds = append(result.Feeds, ConvertFeedConfig(&feed))
	}
	return result
}

func ConvertFeedConfig(fc *FeedConfig) *api.FeedConfig {
	result := &api.FeedConfig{
		Url:         fc.Url,
		HttpHeaders: fc.HttpHeaders,
	}
	if fc.HttpTimeout != nil {
		timeout := fc.HttpTimeout.Milliseconds()
		result.HttpTimeout = &timeout
	}
	switch fc.Parser {
	case GtfsStatic:
		var apiExceptions []*api.FeedConfig_GtfsStaticParser_TransfersExceptions
		for _, exception := range fc.GtfsStaticOptions.TransfersExceptions {
			apiExceptions = append(apiExceptions, &api.FeedConfig_GtfsStaticParser_TransfersExceptions{
				StopId_1: exception.StopId1,
				StopId_2: exception.StopId2,
				Strategy: convertInternalTransfersStrategy(exception.Strategy),
			})
		}
		result.Parser = &api.FeedConfig_GtfsStaticParser_{
			GtfsStaticParser: &api.FeedConfig_GtfsStaticParser{
				TransfersStrategy:   convertInternalTransfersStrategy(fc.GtfsStaticOptions.TransfersStrategy),
				TransfersExceptions: apiExceptions,
			},
		}
	case GtfsRealtime:
		var apiExts []api.GtfsRealtimeExtension
		for _, ext := range fc.GtfsRealtimeOptions.Extensions {
			switch ext {
			case UsNySubwayAlerts:
				apiExts = append(apiExts, api.GtfsRealtimeExtension_US_NY_SUBWAY_ALERTS)
			case UsNySubwayTrips:
				apiExts = append(apiExts, api.GtfsRealtimeExtension_US_NY_SUBWAY_TRIPS)
			}
		}
		result.Parser = &api.FeedConfig_GtfsRealtimeParser_{
			GtfsRealtimeParser: &api.FeedConfig_GtfsRealtimeParser{
				Extensions: apiExts,
			},
		}
	case DirectionRules:
		result.Parser = &api.FeedConfig_DirectionRulesParser_{}
	}
	return result
}

func convertInternalTransfersStrategy(s TransfersStrategy) api.FeedConfig_GtfsStaticParser_TransfersStrategy {
	switch s {
	case Default:
		return api.FeedConfig_GtfsStaticParser_DEFAULT
	case GroupStations:
		return api.FeedConfig_GtfsStaticParser_GROUP_STATIONS
	}
	return api.FeedConfig_GtfsStaticParser_DEFAULT
}

func UnmarshalFromYaml(b []byte) (*SystemConfig, error) {
	var config SystemConfig
	if err := yaml.Unmarshal(b, &config); err != nil {
		return nil, fmt.Errorf("failed to parse Transiter system config Yaml: %w", err)
	}
	return &config, nil
}

func (fc *FeedConfig) MarshalToJson() []byte {
	b, err := json.Marshal(fc)
	if err != nil {
		panic(fmt.Sprintf("unexpected error when marhsalling feed config: %s", err))
	}
	return b
}

func UnmarshalFromJson(b []byte) (*FeedConfig, error) {
	var config FeedConfig
	if err := json.Unmarshal(b, &config); err != nil {
		return nil, err
	}
	return &config, nil
}
