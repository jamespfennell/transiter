// Package servicemaps contains all of the logic for Transiter's service maps features.
package servicemaps

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/jamespfennell/gtfs"
	"github.com/jamespfennell/transiter/internal/db/dbwrappers"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/graph"
	"golang.org/x/exp/slog"
	"google.golang.org/protobuf/encoding/protojson"
)

// UpdateConfig updates the service map configuration for the provided system.
func UpdateConfig(ctx context.Context, querier db.Querier, systemPk int64, configs []*api.ServiceMapConfig) error {
	// TODO: SkipDefaultServiceMaps {
	if len(configs) == 0 {
		sevenAm := float64(7)
		sevenPm := float64(19)
		configs = []*api.ServiceMapConfig{
			{
				Id:        "alltimes",
				Source:    api.ServiceMapConfig_STATIC,
				Threshold: 0.1,
			},
			{
				Id:        "weekday",
				Source:    api.ServiceMapConfig_STATIC,
				Threshold: 0.1,
				StaticOptions: &api.ServiceMapConfig_StaticOptions{
					StartsLaterThan: &sevenAm,
					EndsEarlierThan: &sevenPm,
					Days:            []string{"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"},
				},
			},
			{
				Id:     "realtime",
				Source: api.ServiceMapConfig_REALTIME,
			},
		}
	}
	config, err := querier.ListServiceMapConfigsInSystem(ctx, systemPk)
	if err != nil {
		return nil
	}
	configIDToPk := map[string]int64{}
	for _, config := range config {
		configIDToPk[config.ID] = config.Pk
	}
	for _, newConfig := range configs {
		j, err := protojson.Marshal(newConfig)
		if err != nil {
			return err
		}
		if pk, ok := configIDToPk[newConfig.Id]; ok {
			if err := querier.UpdateServiceMapConfig(ctx, db.UpdateServiceMapConfigParams{
				Pk:     pk,
				Config: j,
			}); err != nil {
				return err
			}
			delete(configIDToPk, newConfig.Id)
		} else {
			if err := querier.InsertServiceMapConfig(ctx, db.InsertServiceMapConfigParams{
				ID:       newConfig.Id,
				SystemPk: systemPk,
				Config:   j,
			}); err != nil {
				return err
			}
		}
	}
	for _, pk := range configIDToPk {
		if err := querier.DeleteServiceMapConfig(ctx, pk); err != nil {
			return err
		}
	}
	return nil
}

type UpdateStaticMapsArgs struct {
	SystemPk    int64
	Trips       []gtfs.ScheduledTrip
	RouteIDToPk map[string]int64
}

// UpdateStaticMaps updates the static service maps
func UpdateStaticMaps(ctx context.Context, querier db.Querier, logger *slog.Logger, args UpdateStaticMapsArgs) error {
	configs, err := ListConfigsInSystem(ctx, querier, logger, args.SystemPk)
	if err != nil {
		return err
	}

	stopIDToStationPk, err := dbwrappers.MapStopIDToStationPk(ctx, querier, args.SystemPk)
	if err != nil {
		return err
	}

	for _, smc := range configs[api.ServiceMapConfig_STATIC] {
		routePkToStopPks := buildStaticMaps(logger, smc.Config, args.RouteIDToPk, stopIDToStationPk, args.Trips)
		for routePk, stopPks := range routePkToStopPks {
			if err := persistMap(ctx, querier, &smc, routePk, stopPks); err != nil {
				return err
			}
		}
	}
	return nil
}

func persistMap(ctx context.Context, querier db.Querier, smc *Config, routePk int64, stopPks []int64) error {
	if err := querier.DeleteServiceMap(ctx, db.DeleteServiceMapParams{
		ConfigPk: smc.Pk,
		RoutePk:  routePk,
	}); err != nil {
		return err
	}
	// TODO: consider not deleting and then inserting
	mapPk, err := querier.InsertServiceMap(ctx, db.InsertServiceMapParams{
		ConfigPk: smc.Pk,
		RoutePk:  routePk,
	})
	if err != nil {
		return err
	}
	var insertParams []db.InsertServiceMapStopParams
	for i, stopPk := range stopPks {
		insertParams = append(insertParams, db.InsertServiceMapStopParams{
			MapPk:    mapPk,
			StopPk:   stopPk,
			Position: int32(i),
		})
	}
	if _, err := querier.InsertServiceMapStop(ctx, insertParams); err != nil {
		return err
	}
	return nil
}

func buildStaticMaps(logger *slog.Logger, smc *api.ServiceMapConfig, routeIDToPk map[string]int64, stopIDToStationPk map[string]int64, trips []gtfs.ScheduledTrip) map[int64][]int64 {
	includedServiceIDs := buildIncludedServiceIDs(smc, trips)

	routePkToKeyToCount := map[int64]map[string]int{}
	for _, routePk := range routeIDToPk {
		routePkToKeyToCount[routePk] = map[string]int{}
	}
	keyToEdges := map[string][]graph.Edge{}
	for _, trip := range trips {
		routePk, ok := routeIDToPk[trip.Route.Id]
		if !ok {
			continue
		}
		if !isIncludedTrip(smc, &trip, includedServiceIDs) {
			continue
		}
		key := calculateTripKey(&trip, stopIDToStationPk)
		routePkToKeyToCount[routePk][key] = routePkToKeyToCount[routePk][key] + 1
		var edges []graph.Edge
		for j := 1; j < len(trip.StopTimes); j++ {
			from, to := j-1, j
			if trip.DirectionId == gtfs.DirectionID_False {
				from, to = j, j-1
			}
			fromLabel, ok := stopIDToStationPk[trip.StopTimes[from].Stop.Id]
			if !ok {
				continue
			}
			toLabel, ok := stopIDToStationPk[trip.StopTimes[to].Stop.Id]
			if !ok {
				continue
			}
			edges = append(edges, graph.Edge{
				FromLabel: fromLabel,
				ToLabel:   toLabel,
			})
		}
		keyToEdges[key] = edges
	}
	routePkToEdges := map[int64]map[graph.Edge]bool{}
	for _, routePk := range routeIDToPk {
		routePkToEdges[routePk] = map[graph.Edge]bool{}
	}
	for routePk, keyToCount := range routePkToKeyToCount {
		totalCount := 0
		for _, count := range keyToCount {
			totalCount += count
		}
		countThreshhold := float64(totalCount) * smc.Threshold
		for key, count := range keyToCount {
			if float64(count) < countThreshhold {
				continue
			}
			for _, edge := range keyToEdges[key] {
				routePkToEdges[routePk][edge] = true
			}
		}
	}

	m := map[int64][]int64{}
	for routePk := range routePkToKeyToCount {
		var err error
		m[routePk], err = buildMap(routePkToEdges[routePk])
		if err != nil {
			logger.Error(fmt.Sprintf("error building static map: %s", err))
			continue
		}
	}
	return m
}

func calculateTripKey(trip *gtfs.ScheduledTrip, stopIDToStationPk map[string]int64) string {
	var stationPks []int64
	for _, stopTime := range trip.StopTimes {
		stationPk, ok := stopIDToStationPk[stopTime.Stop.Id]
		if !ok {
			continue
		}
		stationPks = append(stationPks, stationPk)
	}
	if trip.DirectionId == gtfs.DirectionID_True {
		for i, j := 0, len(stationPks)-1; i < j; i, j = i+1, j-1 {
			stationPks[i], stationPks[j] = stationPks[j], stationPks[i]
		}
	}
	var b strings.Builder
	for _, stationPk := range stationPks {
		b.WriteString(fmt.Sprintf("%d-", stationPk))
	}
	return b.String()
}

// isIncludedTrip returns whether the trip should be included in the service map.
func isIncludedTrip(smc *api.ServiceMapConfig, trip *gtfs.ScheduledTrip, includedServiceIDs map[string]bool) bool {
	if trip.DirectionId == gtfs.DirectionID_Unspecified {
		return false
	}
	if !includedServiceIDs[trip.Service.Id] {
		return false
	}
	if len(trip.StopTimes) == 0 {
		return false
	}
	startTime := trip.StopTimes[0].ArrivalTime
	endTime := trip.StopTimes[len(trip.StopTimes)-1].ArrivalTime
	staticOpts := smc.GetStaticOptions()
	if staticOpts == nil {
		staticOpts = &api.ServiceMapConfig_StaticOptions{}
	}
	c := func(in float64) time.Duration {
		return time.Duration(in * float64(time.Hour))
	}
	if staticOpts.StartsEarlierThan != nil && c(*staticOpts.StartsEarlierThan) < startTime {
		return false
	}
	if staticOpts.StartsLaterThan != nil && c(*staticOpts.StartsLaterThan) > startTime {
		return false
	}
	if staticOpts.EndsEarlierThan != nil && c(*staticOpts.EndsEarlierThan) < endTime {
		return false
	}
	if staticOpts.EndsLaterThan != nil && c(*staticOpts.EndsLaterThan) > endTime {
		return false
	}
	return true
}

// buildIncludedServiceIDs builds a set of all service IDs which are to be used for this service map.
// A trip can be included in this map only if its service is in the set.
//
// The calculation is based on the days field in the service map config and the days fields in the service.
// In general a service must run on at least one day specified in the configuration. However if there are no days specified
// in the configuration then all services are allowed.
func buildIncludedServiceIDs(smc *api.ServiceMapConfig, trips []gtfs.ScheduledTrip) map[string]bool {
	allowedDays := map[string]bool{}
	for _, day := range smc.GetStaticOptions().GetDays() {
		allowedDays[strings.ToLower(day)] = true
	}
	excludedServiceIDs := map[string]bool{}
	includedServiceIDs := map[string]bool{}
	for i := range trips {
		service := trips[i].Service
		if excludedServiceIDs[service.Id] || includedServiceIDs[service.Id] {
			continue
		}
		if len(allowedDays) == 0 {
			includedServiceIDs[service.Id] = true
			continue
		}
		for _, c := range []struct {
			day            string
			serviceRunning bool
		}{
			{"monday", service.Monday},
			{"tuesday", service.Tuesday},
			{"wednesday", service.Wednesday},
			{"thursday", service.Thursday},
			{"friday", service.Friday},
			{"saturday", service.Saturday},
			{"sunday", service.Sunday},
		} {
			if c.serviceRunning && allowedDays[c.day] {
				includedServiceIDs[service.Id] = true
				break
			}
		}
		if !includedServiceIDs[service.Id] {
			excludedServiceIDs[service.Id] = true
		}
	}
	return includedServiceIDs
}

func buildMap(edgesSet map[graph.Edge]bool) ([]int64, error) {
	var edges []graph.Edge
	for edge := range edgesSet {
		edges = append(edges, edge)
	}
	g := graph.NewGraph(edges...)
	orderedNodes, err := graph.SortBasic(g)
	if err != nil {
		return nil, fmt.Errorf("service map cannot be topologically sorted: %w", err)
	}
	stopPks := []int64{}
	for _, node := range orderedNodes {
		stopPks = append(stopPks, node.GetLabel())
	}
	return stopPks, nil
}

// UpdateRealtimeMaps updates the realtime service maps
func UpdateRealtimeMaps(ctx context.Context, querier db.Querier, logger *slog.Logger, systemPk int64, routePks []int64) error {
	configs, err := ListConfigsInSystem(ctx, querier, logger, systemPk)
	if err != nil {
		return err
	}
	for _, routePk := range routePks {
		tripStopPks, err := getTripStopPks(ctx, querier, routePk)
		if err != nil {
			return err
		}

		stopPksSeen := map[int64]bool{}
		var allStopPks []int64
		for _, stopPks := range tripStopPks {
			for _, stopPk := range stopPks {
				if stopPksSeen[stopPk] {
					continue
				}
				stopPksSeen[stopPk] = true
				allStopPks = append(allStopPks, stopPk)
			}
		}
		stopPkToStationPk, err := dbwrappers.MapStopPkToStationPk(ctx, querier, systemPk, allStopPks)
		if err != nil {
			return err
		}

		edges := buildRealtimeMapEdges(tripStopPks, stopPkToStationPk)
		mapAsStopPks, err := buildMap(edges)
		if err != nil {
			logger.DebugCtx(ctx, fmt.Sprintf("error building realtime map: %s", err))
			continue
		}
		for _, smc := range configs[api.ServiceMapConfig_REALTIME] {
			if err := persistMap(ctx, querier, &smc, routePk, mapAsStopPks); err != nil {
				return err
			}
		}
	}
	return nil
}

func getTripStopPks(ctx context.Context, querier db.Querier, routePk int64) ([][]int64, error) {
	rows, err := querier.ListStopPksForRealtimeMap(ctx, routePk)
	if err != nil {
		return nil, err
	}
	var result [][]int64
	var currentTripPk int64 = -1
	var currentDirectionID bool
	var currentStopPks []int64
	updateResult := func() {
		if len(currentStopPks) == 0 {
			return
		}
		if !currentDirectionID {
			reverse(currentStopPks)
		}
		result = append(result, currentStopPks)
		currentStopPks = []int64{}
	}
	for _, row := range rows {
		if row.TripPk != currentTripPk {
			updateResult()
		}
		currentTripPk = row.TripPk
		// The query guarantees that the direction ID column is not null
		currentDirectionID = row.DirectionID.Bool
		currentStopPks = append(currentStopPks, row.StopPk)
	}
	updateResult()
	return result, nil
}

func reverse(s []int64) {
	for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
		s[i], s[j] = s[j], s[i]
	}
}

func buildRealtimeMapEdges(tripStopPks [][]int64, stopPkToStationPk map[int64]int64) map[graph.Edge]bool {
	m := map[graph.Edge]bool{}
	for _, stopPks := range tripStopPks {
		for i := 1; i < len(stopPks); i++ {
			edge := graph.Edge{
				FromLabel: stopPkToStationPk[stopPks[i-1]],
				ToLabel:   stopPkToStationPk[stopPks[i]],
			}
			m[edge] = true
		}
	}
	return m
}

type Config struct {
	Pk     int64
	Config *api.ServiceMapConfig
}

// ListConfigsInSystem lists all of the service map configs in the provided system,
// grouped by source.
func ListConfigsInSystem(ctx context.Context, querier db.Querier, logger *slog.Logger, systemPk int64) (map[api.ServiceMapConfig_Source][]Config, error) {
	rawConfigs, err := querier.ListServiceMapConfigsInSystem(ctx, systemPk)
	if err != nil {
		return nil, err
	}
	configs := map[api.ServiceMapConfig_Source][]Config{}
	for _, rawConfig := range rawConfigs {
		smc := Config{
			Pk:     rawConfig.Pk,
			Config: &api.ServiceMapConfig{},
		}
		if err := protojson.Unmarshal(rawConfig.Config, smc.Config); err != nil {
			slog.ErrorCtx(ctx, fmt.Sprintf("invalid service map config for system_pk=%d, skipping: %s", systemPk, err))
			continue
		}
		configs[smc.Config.GetSource()] = append(configs[smc.Config.GetSource()], smc)
	}
	return configs, nil
}
