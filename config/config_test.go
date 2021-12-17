package config

import (
	"fmt"
	"reflect"
	"testing"
	"time"

	"github.com/jamespfennell/transiter/internal/gen/api"
	"google.golang.org/protobuf/proto"
)

const (
	Url         = "url"
	HeaderKey   = "headerKey"
	HeaderValue = "headerValue"
	StopId1     = "stopId1"
	StopId2     = "stopId2"
)

func TestConvert(t *testing.T) {
	var timeoutMs int64 = 5000
	timeoutDuration := time.Second * 5
	alertsExt := api.GtfsRealtimeExtension_US_NY_SUBWAY_ALERTS

	testCases := []struct {
		apiConfig      *api.FeedConfig
		internalConfig *FeedConfig
	}{
		{
			apiConfig: &api.FeedConfig{
				RequiredForInstall: true,
				AutoUpdateEnabled:  true,
				AutoUpdatePeriod:   &timeoutMs,
			},
			internalConfig: &FeedConfig{
				RequiredForInstall: true,
				AutoUpdateEnabled:  true,
				AutoUpdatePeriod:   &timeoutDuration,
			},
		},
		{
			apiConfig: &api.FeedConfig{
				Url:         Url,
				HttpTimeout: &timeoutMs,
				HttpHeaders: map[string]string{
					HeaderKey: HeaderValue,
				},
			},
			internalConfig: &FeedConfig{
				Url:         Url,
				HttpTimeout: &timeoutDuration,
				HttpHeaders: map[string]string{
					HeaderKey: HeaderValue,
				},
			},
		},
		{
			apiConfig: &api.FeedConfig{
				Parser: &api.FeedConfig_GtfsStaticParser_{
					GtfsStaticParser: &api.FeedConfig_GtfsStaticParser{
						TransfersStrategy: api.FeedConfig_GtfsStaticParser_GROUP_STATIONS,
						TransfersExceptions: []*api.FeedConfig_GtfsStaticParser_TransfersExceptions{
							{
								StopId_1: StopId1,
								StopId_2: StopId2,
								Strategy: api.FeedConfig_GtfsStaticParser_DEFAULT,
							},
						},
					},
				},
			},
			internalConfig: &FeedConfig{
				Parser: GtfsStatic,
				GtfsStaticOptions: GtfsStaticOptions{
					TransfersStrategy: GroupStations,
					TransfersExceptions: []TransfersException{
						{
							StopId1:  StopId1,
							StopId2:  StopId2,
							Strategy: Default,
						},
					},
				},
			},
		},
		{
			apiConfig: &api.FeedConfig{
				Parser: &api.FeedConfig_GtfsRealtimeParser_{
					GtfsRealtimeParser: &api.FeedConfig_GtfsRealtimeParser{
						Extension: &alertsExt,
					},
				},
			},
			internalConfig: &FeedConfig{
				Parser: GtfsRealtime,
				GtfsRealtimeOptions: GtfsRealtimeOptions{
					Extension: UsNySubwayAlerts,
				},
			},
		},
		{
			apiConfig: &api.FeedConfig{
				Parser: &api.FeedConfig_GtfsRealtimeParser_{
					GtfsRealtimeParser: &api.FeedConfig_GtfsRealtimeParser{},
				},
			},
			internalConfig: &FeedConfig{
				Parser:              GtfsRealtime,
				GtfsRealtimeOptions: GtfsRealtimeOptions{},
			},
		},
		{
			apiConfig: &api.FeedConfig{
				Parser: &api.FeedConfig_DirectionRulesParser_{},
			},
			internalConfig: &FeedConfig{
				Parser: DirectionRules,
			},
		},
	}

	for i, tc := range testCases {
		t.Run(fmt.Sprintf("%d-apiToInternal", i), func(t *testing.T) {
			convertedInternalConfig := ConvertApiFeedConfig(tc.apiConfig)
			if !reflect.DeepEqual(convertedInternalConfig, tc.internalConfig) {
				t.Errorf("Converted internal config:\n%+v\nis not equal to the expected config:\n%+v\n",
					convertedInternalConfig, tc.internalConfig)
			}
		})
		t.Run(fmt.Sprintf("%d-internalToApi", i), func(t *testing.T) {
			convertedApiConfig := ConvertFeedConfig(tc.internalConfig)
			if !proto.Equal(convertedApiConfig, tc.apiConfig) {
				t.Errorf("Converted API config:\n%+v\nis not equal to the expected config:\n%+v\n",
					convertedApiConfig, tc.apiConfig)
			}
		})
	}
}
