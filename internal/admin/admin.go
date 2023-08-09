// Package admin contains the implementation of the Transiter admin API.
package admin

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"text/template"

	"github.com/ghodss/yaml"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamespfennell/transiter/internal/db/constants"
	"github.com/jamespfennell/transiter/internal/gen/api"
	"github.com/jamespfennell/transiter/internal/gen/db"
	"github.com/jamespfennell/transiter/internal/monitoring"
	"github.com/jamespfennell/transiter/internal/public/errors"
	"github.com/jamespfennell/transiter/internal/scheduler"
	"github.com/jamespfennell/transiter/internal/servicemaps"
	"github.com/jamespfennell/transiter/internal/update"
	"golang.org/x/exp/slog"
	"google.golang.org/protobuf/encoding/protojson"
)

// Service implements the Transiter admin API.
type Service struct {
	pool       *pgxpool.Pool
	scheduler  scheduler.Scheduler
	logger     *slog.Logger
	levelVar   *slog.LevelVar
	monitoring monitoring.Monitoring
}

func New(pool *pgxpool.Pool, scheduler scheduler.Scheduler, logger *slog.Logger, levelVar *slog.LevelVar, monitoring monitoring.Monitoring) *Service {
	return &Service{
		pool:       pool,
		scheduler:  scheduler,
		logger:     logger,
		levelVar:   levelVar,
		monitoring: monitoring,
	}
}

func (s *Service) GetSystemConfig(ctx context.Context, req *api.GetSystemConfigRequest) (*api.SystemConfig, error) {
	reply := &api.SystemConfig{}
	err := pgx.BeginTxFunc(ctx, s.pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		system, err := querier.GetSystem(ctx, req.SystemId)
		if err != nil {
			if err == pgx.ErrNoRows {
				err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
			}
			return err
		}
		reply.Name = system.Name
		feeds, err := querier.ListFeeds(ctx, system.Pk)
		if err != nil {
			return err
		}
		for _, feed := range feeds {
			feed := feed
			var feedConfig api.FeedConfig
			if err := protojson.Unmarshal([]byte(feed.Config), &feedConfig); err != nil {
				return err
			}
			reply.Feeds = append(reply.Feeds, &feedConfig)
		}
		return nil
	})
	return reply, err
}

func (s *Service) InstallOrUpdateSystem(ctx context.Context, req *api.InstallOrUpdateSystemRequest) (*api.InstallOrUpdateSystemReply, error) {
	logger := s.logger.With(slog.String("system_id", req.GetSystemId()))
	logger.InfoCtx(ctx, "recieved install or update systm request")

	var err error
	var systemConfig *api.SystemConfig
	switch c := req.GetConfig().(type) {
	case *api.InstallOrUpdateSystemRequest_SystemConfig:
		systemConfig = c.SystemConfig
	case *api.InstallOrUpdateSystemRequest_YamlConfig:
		var rawConfig []byte
		switch s := c.YamlConfig.Source.(type) {
		case *api.TextConfig_Url:
			rawConfig, err = getRawSystemConfigFromURL(s.Url)
			if err != nil {
				return nil, err
			}
		case *api.TextConfig_Content:
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
	logger.InfoCtx(ctx, fmt.Sprintf("config: %+v", systemConfig))

	var keepGoing bool
	if err := pgx.BeginTxFunc(ctx, s.pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		var err error
		keepGoing, err = upsertSystemEntry(ctx, querier, req.SystemId, systemConfig.Name, req.InstallOnly)
		return err
	}); err != nil {
		return nil, err
	}
	if keepGoing {
		go func() {
			// TODO: can we wire through the context on the server?
			ctx := context.Background()
			err := s.performInstall(ctx, req.SystemId, systemConfig)
			if err != nil {
				logger.ErrorCtx(ctx, fmt.Sprintf("install or update failed: %s", err))
			}
			if err := pgx.BeginTxFunc(ctx, s.pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
				return markSystemInstallFinished(ctx, db.New(tx), req.SystemId, err)
			}); err != nil {
				logger.ErrorCtx(ctx, fmt.Sprintf("failed to mark install or update finished: %s", err))
				return
			}
			logger.InfoCtx(ctx, "install or update finished")
			s.scheduler.ResetSystem(ctx, req.SystemId)
		}()
	}
	return &api.InstallOrUpdateSystemReply{}, nil
}

func upsertSystemEntry(ctx context.Context, querier db.Querier, systemID string, systemName string, installOnly bool) (bool, error) {
	system, err := querier.GetSystem(ctx, systemID)
	if err == pgx.ErrNoRows {
		_, err = querier.InsertSystem(ctx, db.InsertSystemParams{
			ID:     systemID,
			Name:   systemName,
			Status: constants.Installing,
		})
		return true, err
	}
	if err != nil {
		return false, err
	}
	if installOnly && system.Status == constants.Active {
		return false, nil
	}
	err = querier.UpdateSystemStatus(ctx, db.UpdateSystemStatusParams{
		Pk:     system.Pk,
		Status: constants.Updating,
	})
	return true, err
}

func (s *Service) performInstall(ctx context.Context, systemID string, systemConfig *api.SystemConfig) error {
	if err := pgx.BeginTxFunc(ctx, s.pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		return upsertSystemMetadata(ctx, db.New(tx), systemID, systemConfig)
	}); err != nil {
		return err
	}
	for _, feed := range systemConfig.GetFeeds() {
		update.NormalizeFeedConfig(feed)
		if !feed.GetRequiredForInstall() {
			continue
		}
		if _, err := update.Update(ctx, s.logger, s.pool, s.monitoring, systemID, feed.Id, false); err != nil {
			return err
		}
	}
	return nil
}

func upsertSystemMetadata(ctx context.Context, querier db.Querier, systemID string, config *api.SystemConfig) error {
	system, err := querier.GetSystem(ctx, systemID)
	if err != nil {
		return err
	}
	if err := querier.UpdateSystem(ctx, db.UpdateSystemParams{
		Pk:   system.Pk,
		Name: config.Name,
	}); err != nil {
		return err
	}

	// Service maps need to be updated before feeds. This is because updating a feed config may
	// trigger a feed update (if required_for_install=true) which may require the updated service
	// map config. This is tested in the end-to-end tests.
	if err := servicemaps.UpdateConfig(ctx, querier, system.Pk, config.ServiceMaps); err != nil {
		return err
	}

	feeds, err := querier.ListFeeds(ctx, system.Pk)
	if err != nil {
		return err
	}
	feedIDToPk := map[string]int64{}
	for _, feed := range feeds {
		feedIDToPk[feed.ID] = feed.Pk
	}

	for _, newFeed := range config.Feeds {
		j, err := protojson.Marshal(newFeed)
		if err != nil {
			return err
		}
		if pk, ok := feedIDToPk[newFeed.Id]; ok {
			if err := querier.UpdateFeed(ctx, db.UpdateFeedParams{
				FeedPk: pk,
				Config: string(j),
			}); err != nil {
				return err
			}
			delete(feedIDToPk, newFeed.Id)
		} else {
			// TODO: is there a lint to detect not handling the error here?
			querier.InsertFeed(ctx, db.InsertFeedParams{
				ID:       newFeed.Id,
				SystemPk: system.Pk,
				Config:   string(j),
			})
		}
	}
	for _, pk := range feedIDToPk {
		querier.DeleteFeed(ctx, pk)
	}
	return nil
}

func markSystemInstallFinished(ctx context.Context, querier db.Querier, systemID string, installErr error) error {
	system, err := querier.GetSystem(ctx, systemID)
	if err != nil {
		return err
	}
	var newStatus string
	if installErr != nil {
		if system.Status == constants.Installing {
			newStatus = constants.InstallFailed
		} else {
			newStatus = constants.UpdateFailed
		}
	} else {
		newStatus = constants.Active
	}
	return querier.UpdateSystemStatus(ctx, db.UpdateSystemStatusParams{
		Pk:     system.Pk,
		Status: newStatus,
	})
}

func (s *Service) DeleteSystem(ctx context.Context, req *api.DeleteSystemRequest) (*api.DeleteSystemReply, error) {
	logger := s.logger.With(slog.String("system_id", req.GetSystemId()))
	logger.InfoCtx(ctx, "received delete system request")

	if err := pgx.BeginTxFunc(ctx, s.pool, pgx.TxOptions{}, func(tx pgx.Tx) error {
		querier := db.New(tx)
		system, err := querier.GetSystem(ctx, req.SystemId)
		if err != nil {
			if err == pgx.ErrNoRows {
				err = errors.NewNotFoundError(fmt.Sprintf("system %q not found", req.SystemId))
			}
			return err
		}
		return querier.DeleteSystem(ctx, system.Pk)
	}); err != nil {
		return nil, err
	}
	if err := s.scheduler.ResetSystem(ctx, req.SystemId); err != nil {
		return nil, err
	}
	logger.InfoCtx(ctx, "system deleted")
	return &api.DeleteSystemReply{}, nil
}

func getRawSystemConfigFromURL(url string) ([]byte, error) {
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

func parseSystemConfigYaml(rawContent []byte, isTemplate bool, templateArgs map[string]string) (*api.SystemConfig, error) {
	if !isTemplate {
		return unmarshalFromYaml(rawContent)
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
	return unmarshalFromYaml(b.Bytes())
}

func unmarshalFromYaml(y []byte) (*api.SystemConfig, error) {
	j, err := yaml.YAMLToJSON(y)
	if err != nil {
		return nil, err
	}
	var config api.SystemConfig
	if err := protojson.Unmarshal(j, &config); err != nil {
		return nil, err
	}
	return &config, nil
}
