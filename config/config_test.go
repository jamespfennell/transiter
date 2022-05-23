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
	URL          = "url"
	HeaderKey    = "headerKey"
	HeaderValue  = "headerValue"
	StopID1      = "stopID1"
	StopID2      = "stopID2"
	ServiceMapID = "serviceMapId"
)

func TestConvertFeedConfig(t *testing.T) {
	var timeoutMs int64 = 5000
	timeoutDuration := time.Second * 5
	alertsExt := api.GtfsRealtimeExtension_US_NY_SUBWAY_ALERTS

	testCases := []struct {
		apiConfig      *api.FeedConfig
		internalConfig *FeedConfig
	}{
		{
			apiConfig: &api.FeedConfig{
				RequiredForInstall:    true,
				PeriodicUpdateEnabled: true,
				PeriodicUpdatePeriod:  &timeoutMs,
			},
			internalConfig: &FeedConfig{
				RequiredForInstall:    true,
				PeriodicUpdateEnabled: true,
				PeriodicUpdatePeriod:  &timeoutDuration,
			},
		},
		{
			apiConfig: &api.FeedConfig{
				Url:         URL,
				HttpTimeout: &timeoutMs,
				HttpHeaders: map[string]string{
					HeaderKey: HeaderValue,
				},
			},
			internalConfig: &FeedConfig{
				URL:         URL,
				HTTPTimeout: &timeoutDuration,
				HTTPHeaders: map[string]string{
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
								StopId_1: StopID1,
								StopId_2: StopID2,
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
							StopID1:  StopID1,
							StopID2:  StopID2,
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
				Parser: &api.FeedConfig_NyctSubwayCsvParser_{},
			},
			internalConfig: &FeedConfig{
				Parser: NyctSubwayCsv,
			},
		},
	}

	for i, tc := range testCases {
		t.Run(fmt.Sprintf("%d-apiToInternal", i), func(t *testing.T) {
			convertedInternalConfig := ConvertAPIFeedConfig(tc.apiConfig)
			if !reflect.DeepEqual(convertedInternalConfig, tc.internalConfig) {
				t.Errorf("Converted internal config:\n%+v\nis not equal to the expected config:\n%+v\n",
					convertedInternalConfig, tc.internalConfig)
			}
		})
		t.Run(fmt.Sprintf("%d-internalToApi", i), func(t *testing.T) {
			convertedAPIConfig := ConvertFeedConfig(tc.internalConfig)
			if !proto.Equal(convertedAPIConfig, tc.apiConfig) {
				t.Errorf("Converted API config:\n%+v\nis not equal to the expected config:\n%+v\n",
					convertedAPIConfig, tc.apiConfig)
			}
		})
	}
}

func TestConvertServiceMapsConfig(t *testing.T) {
	t1Duration := 3 * time.Hour
	t1Int64 := int64(180)
	t2Duration := time.Hour + 12*time.Minute
	t2Int64 := int64(72)

	testCases := []struct {
		apiConfig      *api.ServiceMapConfig
		internalConfig *ServiceMapConfig
	}{
		{
			apiConfig: &api.ServiceMapConfig{
				Id:                     ServiceMapID,
				Source:                 &api.ServiceMapConfig_RealtimeSource{},
				DefaultForRoutesAtStop: true,
				DefaultForStopsInRoute: false,
			},
			internalConfig: &ServiceMapConfig{
				ID:                     ServiceMapID,
				Source:                 ServiceMapSourceRealtime,
				DefaultForRoutesAtStop: true,
				DefaultForStopsInRoute: false,
			},
		},
		{
			apiConfig: &api.ServiceMapConfig{
				Id: ServiceMapID,
				Source: &api.ServiceMapConfig_StaticSource{
					StaticSource: &api.ServiceMapConfig_Static{
						StartsEarlierThan: &t1Int64,
						EndsEarlierThan:   &t2Int64,
						Days:              []string{"Monday", "Tuesday"},
					},
				},
				DefaultForRoutesAtStop: false,
				DefaultForStopsInRoute: true,
			},
			internalConfig: &ServiceMapConfig{
				ID:                     ServiceMapID,
				Source:                 ServiceMapSourceStatic,
				StartsEarlierThan:      &t1Duration,
				EndsEarlierThan:        &t2Duration,
				Days:                   []string{"Monday", "Tuesday"},
				DefaultForRoutesAtStop: false,
				DefaultForStopsInRoute: true,
			},
		},
	}

	for i, tc := range testCases {
		t.Run(fmt.Sprintf("%d-apiToInternal", i), func(t *testing.T) {
			convertedInternalConfig := ConvertAPIServiceMapConfig(tc.apiConfig)
			if !reflect.DeepEqual(convertedInternalConfig, tc.internalConfig) {
				t.Errorf("Converted internal config:\n%+v\nis not equal to the expected config:\n%+v\n",
					convertedInternalConfig, tc.internalConfig)
			}
		})
		t.Run(fmt.Sprintf("%d-internalToApi", i), func(t *testing.T) {
			convertedAPIConfig := ConvertServiceMapConfig(tc.internalConfig)
			if !proto.Equal(convertedAPIConfig, tc.apiConfig) {
				t.Errorf("Converted API config:\n%+v\nis not equal to the expected config:\n%+v\n",
					convertedAPIConfig, tc.apiConfig)
			}
		})
	}
}
