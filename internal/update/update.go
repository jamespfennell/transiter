package update

import (
	"context"
	"database/sql"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/apihelpers"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/parse"
	"github.com/jamespfennell/transiter/parse/gtfsstatic"
)

func CreateAndRun(ctx context.Context, database *sql.DB, systemId, feedId string) error {
	runInTx := func(f func(querier db.Querier) error) error {
		tx, err := database.BeginTx(ctx, nil)
		if err != nil {
			return err
		}
		defer tx.Rollback()
		err = f(db.New(tx))
		if err != nil {
			return err
		}
		tx.Commit()
		return nil
	}
	var feedPk *int64
	if err := runInTx(func(querier db.Querier) error {
		var err error
		*feedPk, err = CreateInsideTx(ctx, querier, systemId, feedId)
		return err
	}); err != nil {
		return err
	}
	// TODO: mark update as IN_PROGRESS
	return runInTx(func(querier db.Querier) error {
		return RunInsideTx(ctx, querier, *feedPk)
	})
}

func CreateAndRunInsideTx(ctx context.Context, querier db.Querier, systemId, feedId string) error {
	updatePk, err := CreateInsideTx(ctx, querier, systemId, feedId)
	if err != nil {
		return err
	}
	return RunInsideTx(ctx, querier, updatePk)
}

func CreateInsideTx(ctx context.Context, querier db.Querier, systemId, feedId string) (int64, error) {
	log.Printf("Creating update for %s/%s\n", systemId, feedId)
	feed, err := querier.GetFeedInSystem(ctx, db.GetFeedInSystemParams{
		SystemID: systemId,
		FeedID:   feedId,
	})
	if err != nil {
		return 0, err
	}
	return querier.InsertFeedUpdate(ctx, db.InsertFeedUpdateParams{
		FeedPk: feed.Pk,
		Status: "CREATED",
	})
}

func RunInsideTx(ctx context.Context, querier db.Querier, updatePk int64) error {
	feed, err := querier.GetFeedForUpdate(ctx, updatePk)
	if err != nil {
		log.Printf("Error update for pk=%d\n", updatePk)
		return err
	}
	feedConfig, err := config.UnmarshalFromJson([]byte(feed.Config))
	if err != nil {
		return fmt.Errorf("failed to parse feed config in the DB: %w", err)
	}
	content, err := getFeedContent(ctx, feedConfig)
	if err != nil {
		return err
	}
	var parser parse.Parser
	switch feedConfig.Parser {
	case config.GtfsStatic:
		parser = &gtfsstatic.Parser{
			Options: &feedConfig.GtfsStaticOptions,
		}
	default:
		return fmt.Errorf("unknown parser %q", feedConfig.Parser)
	}
	parsedEntities, err := parser.Parse(ctx, content)
	if err != nil {
		return err
	}
	runner := runner{
		ctx:      ctx,
		querier:  querier,
		systemPk: feed.SystemPk,
		feedPk:   feed.Pk,
		updatePk: updatePk,
	}
	fmt.Printf("Parse entites: %+v\n", parsedEntities)
	return runner.run(parsedEntities)
}

func getFeedContent(ctx context.Context, feedConfig *config.FeedConfig) ([]byte, error) {
	client := http.Client{
		Timeout: 5 * time.Second,
	}
	if feedConfig.HttpTimeout != nil {
		client.Timeout = *feedConfig.HttpTimeout
	}
	req, err := http.NewRequestWithContext(ctx, "GET", feedConfig.Url, nil)
	if err != nil {
		return nil, err
	}
	for key, value := range feedConfig.HttpHeaders {
		req.Header.Add(key, value)
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}

type runner struct {
	ctx      context.Context
	querier  db.Querier
	systemPk int64
	feedPk   int64
	updatePk int64
}

func (r *runner) run(parsedEntities *parse.Result) error {
	agencyIdToPk, err := r.updateAgencies(parsedEntities.Agencies)
	if err != nil {
		return err
	}
	_, err = r.updateRoutes(parsedEntities.Routes, agencyIdToPk)
	if err != nil {
		return err
	}
	return nil
}

func (r *runner) updateAgencies(agencies []parse.Agency) (map[string]int64, error) {
	idToPk, err := buildAgencyIdToPkMap(r.ctx, r.querier, r.systemPk)
	if err != nil {
		return nil, err
	}
	for _, agency := range agencies {
		var err error
		pk, ok := idToPk[agency.Id]
		if ok {
			err = r.querier.UpdateAgency(r.ctx, db.UpdateAgencyParams{
				Pk:       pk,
				SourcePk: r.updatePk,
				Name:     agency.Name,
				Url:      agency.Url,
				Timezone: agency.Timezone,
				Language: apihelpers.ConvertNullString(agency.Language),
				Phone:    apihelpers.ConvertNullString(agency.Phone),
				FareUrl:  apihelpers.ConvertNullString(agency.FareUrl),
				Email:    apihelpers.ConvertNullString(agency.Email),
			})
		} else {
			pk, err = r.querier.InsertAgency(r.ctx, db.InsertAgencyParams{
				ID:       agency.Id,
				SystemPk: r.systemPk,
				SourcePk: r.updatePk,
				Name:     agency.Name,
				Url:      agency.Url,
				Timezone: agency.Timezone,
				Language: apihelpers.ConvertNullString(agency.Language),
				Phone:    apihelpers.ConvertNullString(agency.Phone),
				FareUrl:  apihelpers.ConvertNullString(agency.FareUrl),
				Email:    apihelpers.ConvertNullString(agency.Email),
			})
			idToPk[agency.Id] = pk
		}
		if err != nil {
			return nil, err
		}
	}
	deletedIds, err := r.querier.DeleteStaleAgencies(r.ctx, db.DeleteStaleAgenciesParams{
		FeedPk:   r.feedPk,
		UpdatePk: r.updatePk,
	})
	if err != nil {
		return nil, err
	}
	for _, id := range deletedIds {
		delete(idToPk, id)
	}
	return idToPk, nil
}

func (r *runner) updateRoutes(routes []parse.Route, agencyIdToPk map[string]int64) (map[string]int64, error) {
	idToPk, err := buildRouteIdToPkMap(r.ctx, r.querier, r.systemPk)
	if err != nil {
		return nil, err
	}
	for _, route := range routes {
		agencyPk, ok := agencyIdToPk[route.Agency.Id]
		if !ok {
			log.Printf("no agency %q in the database; skipping route %q", route.Agency.Id, route.Id)
			continue
		}
		pk, ok := idToPk[route.Id]
		if ok {
			err = r.querier.UpdateRoute(r.ctx, db.UpdateRouteParams{
				Pk:                pk,
				SourcePk:          r.updatePk,
				Color:             route.Color,
				TextColor:         route.TextColor,
				ShortName:         apihelpers.ConvertNullString(route.ShortName),
				LongName:          apihelpers.ConvertNullString(route.LongName),
				Description:       apihelpers.ConvertNullString(route.Description),
				Url:               apihelpers.ConvertNullString(route.Url),
				SortOrder:         apihelpers.ConvertNullInt32(route.SortOrder),
				Type:              route.Type.String(),
				ContinuousPickup:  route.ContinuousPickup.String(),
				ContinuousDropOff: route.ContinuousDropOff.String(),
				AgencyPk:          agencyPk,
			})
		} else {
			pk, err = r.querier.InsertRoute(r.ctx, db.InsertRouteParams{
				ID:                route.Id,
				SystemPk:          r.systemPk,
				SourcePk:          r.updatePk,
				Color:             route.Color,
				TextColor:         route.TextColor,
				ShortName:         apihelpers.ConvertNullString(route.ShortName),
				LongName:          apihelpers.ConvertNullString(route.LongName),
				Description:       apihelpers.ConvertNullString(route.Description),
				Url:               apihelpers.ConvertNullString(route.Url),
				SortOrder:         apihelpers.ConvertNullInt32(route.SortOrder),
				Type:              route.Type.String(),
				ContinuousPickup:  route.ContinuousPickup.String(),
				ContinuousDropOff: route.ContinuousDropOff.String(),
				AgencyPk:          agencyPk,
			})
			idToPk[route.Id] = pk
		}
		if err != nil {
			return nil, err
		}
	}
	deletedIds, err := r.querier.DeleteStaleRoutes(r.ctx, db.DeleteStaleRoutesParams{
		FeedPk:   r.feedPk,
		UpdatePk: r.updatePk,
	})
	if err != nil {
		return nil, err
	}
	for _, id := range deletedIds {
		delete(idToPk, id)
	}
	return idToPk, nil
}

func buildAgencyIdToPkMap(ctx context.Context, querier db.Querier, systemPk int64) (map[string]int64, error) {
	idToPk := map[string]int64{}
	rows, err := querier.MapAgencyPkToIdInSystem(ctx, systemPk)
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		idToPk[row.ID] = row.Pk
	}
	return idToPk, nil
}

func buildRouteIdToPkMap(ctx context.Context, querier db.Querier, systemPk int64) (map[string]int64, error) {
	idToPk := map[string]int64{}
	rows, err := querier.MapRoutePkToIdInSystem(ctx, systemPk)
	if err != nil {
		return nil, err
	}
	for _, row := range rows {
		idToPk[row.ID] = row.Pk
	}
	return idToPk, nil
}