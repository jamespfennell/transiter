// Package admin contains the implementation of the Transiter admin service.
package admin

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"text/template"
	"time"

	"github.com/jackc/pgx/v4"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/jamespfennell/transiter/config"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update"
)

// Service implements the Transiter admin service.
type Service struct {
	pool      *pgxpool.Pool
	scheduler *scheduler.Scheduler
	api.UnimplementedTransiterAdminServer
}

func New(pool *pgxpool.Pool, scheduler *scheduler.Scheduler) *Service {
	return &Service{
		pool:      pool,
		scheduler: scheduler,
	}
}

func (s *Service) GetSystemConfig(ctx context.Context, req *api.GetSystemConfigRequest) (*api.SystemConfig, error) {
	tx, err := s.pool.BeginTx(ctx, pgx.TxOptions{})
	if err != nil {
		return nil, err
	}
	defer tx.Rollback(ctx)
	querier := db.New(tx)

	system, err := querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}
	feeds, err := querier.ListFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}

	reply := &api.SystemConfig{
		Name: system.Name,
	}
	for _, feed := range feeds {
		feed := feed
		var feedConfig config.FeedConfig
		if err := json.Unmarshal([]byte(feed.Config), &feedConfig); err != nil {
			log.Panicln("Failed to unmarshal feed config from the DB:", err)
			return nil, err
		}
		reply.Feeds = append(reply.Feeds, config.ConvertFeedConfig(&feedConfig))
	}
	return reply, tx.Commit(ctx)
}

func (s *Service) InstallOrUpdateSystem(ctx context.Context, req *api.InstallOrUpdateSystemRequest) (*api.InstallOrUpdateSystemReply, error) {
	log.Printf("Recieved install or update request for system %q", req.SystemId)
	tx, err := s.pool.BeginTx(ctx, pgx.TxOptions{})
	if err != nil {
		return nil, err
	}
	defer tx.Rollback(ctx)
	querier := db.New(tx)

	var systemConfig *config.SystemConfig
	switch c := req.GetConfig().(type) {
	case *api.InstallOrUpdateSystemRequest_SystemConfig:
		systemConfig = config.ConvertApiSystemConfig(c.SystemConfig)
	case *api.InstallOrUpdateSystemRequest_YamlConfig:
		var rawConfig []byte
		switch s := c.YamlConfig.Source.(type) {
		case *api.YamlConfig_Url:
			rawConfig, err = getRawSystemConfigFromUrl(s.Url)
			if err != nil {
				return nil, err
			}
		case *api.YamlConfig_Content:
			rawConfig = []byte(s.Content)
		default:
			return nil, fmt.Errorf("no system configuration provided")
		}
		systemConfig, err = parseSystemConfigYaml(rawConfig, c.YamlConfig.GetIsTemplate(), c.YamlConfig.GetTemplateArgs())
		if err != nil {
			return nil, err
		}
	default:
		return nil, fmt.Errorf("no system configuration provided")
	}
	log.Printf("Config for install/update for system %s:\n%+v\n", req.SystemId, systemConfig)

	{
		system, err := querier.GetSystem(ctx, req.SystemId)
		if err == pgx.ErrNoRows {
			if _, err = querier.InsertSystem(ctx, db.InsertSystemParams{
				ID:     req.SystemId,
				Name:   systemConfig.Name,
				Status: "ACTIVE",
			}); err != nil {
				return nil, err
			}
		} else if err != nil {
			return nil, err
		} else {
			if err = querier.UpdateSystem(ctx, db.UpdateSystemParams{
				Pk:   system.Pk,
				Name: systemConfig.Name,
			}); err != nil {
				return nil, err
			}
		}
	}
	system, err := querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		return nil, err
	}

	// Service maps need to be updated before feeds. This is because updating a feed config may
	// trigger a feed update (if required_for_install=true) which may require the updated service
	// map config. This is tested in the end-to-end tests.
	if err := servicemaps.UpdateConfig(ctx, querier, system.Pk, systemConfig.ServiceMaps); err != nil {
		return nil, err
	}

	feeds, err := querier.ListFeedsInSystem(ctx, system.Pk)
	if err != nil {
		return nil, err
	}
	feedIdToPk := map[string]int64{}
	for _, feed := range feeds {
		feedIdToPk[feed.ID] = feed.Pk
	}

	for _, newFeed := range systemConfig.Feeds {
		if pk, ok := feedIdToPk[newFeed.Id]; ok {
			if err := querier.UpdateFeed(ctx, db.UpdateFeedParams{
				FeedPk:                pk,
				PeriodicUpdateEnabled: newFeed.PeriodicUpdateEnabled,
				PeriodicUpdatePeriod:  convertNullDuration(newFeed.PeriodicUpdatePeriod),
				Config:                string(newFeed.MarshalToJson()),
			}); err != nil {
				return nil, err
			}
			delete(feedIdToPk, newFeed.Id)
		} else {
			// TODO: is there a lint to detect not handling the error here?
			querier.InsertFeed(ctx, db.InsertFeedParams{
				ID:                    newFeed.Id,
				SystemPk:              system.Pk,
				PeriodicUpdateEnabled: newFeed.PeriodicUpdateEnabled,
				PeriodicUpdatePeriod:  convertNullDuration(newFeed.PeriodicUpdatePeriod),
				Config:                string(newFeed.MarshalToJson()),
			})
		}
		if newFeed.RequiredForInstall {
			if err := update.CreateAndRunInExistingTx(ctx, querier, req.SystemId, newFeed.Id); err != nil {
				return nil, err
			}
		}
	}
	for _, pk := range feedIdToPk {
		querier.DeleteFeed(ctx, pk)
	}

	if err = tx.Commit(ctx); err != nil {
		return nil, err
	}
	log.Printf("Installed system %q\n", system.ID)
	s.scheduler.Reset(ctx, req.SystemId)
	return &api.InstallOrUpdateSystemReply{}, nil
}

func (s *Service) DeleteSystem(ctx context.Context, req *api.DeleteSystemRequest) (*api.DeleteSystemReply, error) {
	log.Printf("Recieved delete request for system %q", req.SystemId)
	tx, err := s.pool.BeginTx(ctx, pgx.TxOptions{})
	defer tx.Rollback(ctx)
	if err != nil {
		return nil, err
	}
	querier := db.New(tx)

	system, err := querier.GetSystem(ctx, req.SystemId)
	if err != nil {
		if err == pgx.ErrNoRows {
			err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
		}
		return nil, err
	}

	if err := querier.DeleteSystem(ctx, system.Pk); err != nil {
		return nil, err
	}
	if err := tx.Commit(ctx); err != nil {
		return nil, err
	}
	log.Printf("Deleted system %q", req.SystemId)
	s.scheduler.Reset(ctx, req.SystemId)
	return &api.DeleteSystemReply{}, nil
}

func getRawSystemConfigFromUrl(url string) ([]byte, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to read transit system config from URL %q: %w", url, err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read transit system config from URL %q: %w", url, err)
	}
	return body, nil
}

func parseSystemConfigYaml(rawContent []byte, isTemplate bool, templateArgs map[string]string) (*config.SystemConfig, error) {
	if !isTemplate {
		return config.UnmarshalFromYaml(rawContent)
	}
	type Input struct {
		Args map[string]string
	}
	input := Input{Args: templateArgs}
	tmpl, err := template.New("transiter-system-config").Parse(string(rawContent))
	if err != nil {
		return nil, fmt.Errorf("failed to parse input as a Go text template: %w", err)
	}
	var b bytes.Buffer
	err = tmpl.Execute(&b, input)
	if err != nil {
		return nil, fmt.Errorf("failed to parse input as a Go text template: %w", err)
	}
	return config.UnmarshalFromYaml(b.Bytes())
}

// TODO: move to convert/converters
func convertNullDuration(d *time.Duration) sql.NullInt32 {
	if d == nil {
		return sql.NullInt32{}
	}
	return sql.NullInt32{
		Valid: true,
		Int32: int32(d.Milliseconds()),
	}
}
