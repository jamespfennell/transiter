package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"strings"

	"github.com/jamespfennell/transiter/internal/argsflag"
	"github.com/jamespfennell/transiter/internal/client"
	"github.com/jamespfennell/transiter/internal/server"
	"github.com/jamespfennell/transiter/internal/version"
	"github.com/urfave/cli/v2"
	"golang.org/x/exp/slog"
)

func main() {
	argsMap := map[string]string{}
	app := &cli.App{
		Name:  "Transiter",
		Usage: "web service for transit data",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:    "addr",
				Aliases: []string{"a"},
				Usage:   "address of the Transiter server's gRPC admin API",
				Value:   "localhost:8083",
			},
		},
		Commands: []*cli.Command{
			{
				Name:  "delete",
				Usage: "delete a transit system",
				Action: func(c *cli.Context) error {
					if c.Args().Len() == 0 {
						return fmt.Errorf("must provide the ID of the system to delete")
					}
					return clientAction(func(ctx context.Context, client *client.Client) error {
						return client.DeleteSystem(ctx, c.Args().Get(0))
					})(c)
				},
			},
			{
				Name:  "install",
				Usage: "install a transit system",
				Flags: []cli.Flag{
					&cli.BoolFlag{
						Name:    "file",
						Aliases: []string{"f"},
						Usage:   "interpret the second argument as a local file path",
						Value:   false,
					},
					&cli.BoolFlag{
						Name:  "template",
						Usage: "indicates that the input file is a Go template",
						Value: false,
					},
					&cli.BoolFlag{
						Name:    "update",
						Aliases: []string{"u"},
						Usage:   "if the system is already installed, update it with the provided config",
						Value:   false,
					},
					argsflag.NewCliFlag("arg", "", argsMap),
				},
				Action: func(c *cli.Context) error {
					if c.Args().Len() == 0 {
						return fmt.Errorf("must provide the ID of the system to delete")
					}
					// TODO: pass the file name using --file and url using --url
					if c.Args().Len() == 1 {
						return fmt.Errorf("must provide a URL or file path for the transit system Yaml config")
					}
					args := client.InstallSystemArgs{
						SystemID:     c.Args().Get(0),
						ConfigPath:   c.Args().Get(1),
						IsFile:       c.Bool("file"),
						AllowUpdate:  c.Bool("update"),
						IsTemplate:   c.Bool("template") || c.IsSet("arg"),
						TemplateArgs: c.Value("arg").(map[string]string),
					}
					return clientAction(func(ctx context.Context, client *client.Client) error {
						return client.InstallSystem(ctx, args)
					})(c)
				},
			},
			{
				Name:  "list",
				Usage: "list all installed transit systems",
				Action: clientAction(func(ctx context.Context, client *client.Client) error {
					return client.ListSystems(ctx)
				}),
			},
			{
				Name:  "log-level",
				Usage: "get or set the log level",
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:  "set",
						Usage: "The new value of the log level. If not set, the current log level is just printed.",
						Value: "",
					},
				},
				Action: func(c *cli.Context) error {
					return clientAction(func(ctx context.Context, client *client.Client) error {
						if logLevel := c.String("set"); logLevel != "" {
							return client.SetLogLevel(ctx, logLevel)
						}
						return client.GetLogLevel(ctx)
					})(c)
				},
			},
			{
				Name:  "scheduler",
				Usage: "perform operations on the Transiter feed update scheduler",
				Subcommands: []*cli.Command{
					{
						Name:  "status",
						Usage: "list the active periodic feed update tasks",
						Action: clientAction(func(ctx context.Context, client *client.Client) error {
							return client.SchedulerStatus(ctx)
						}),
					},
					{
						Name:  "reset",
						Usage: "reset all of the periodic feed update tasks",
						Action: clientAction(func(ctx context.Context, client *client.Client) error {
							return client.ResetScheduler(ctx)
						}),
					},
				},
			},
			{
				Name:  "server",
				Usage: "run a Transiter server",
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:  "public-http-addr",
						Usage: "Address the public HTTP server will listen on. Set to - to disable the public HTTP API.",
						Value: "0.0.0.0:8080",
					},
					&cli.StringFlag{
						Name:  "public-grpc-addr",
						Usage: "Address the public gRPC server will listen on. Set to - to disable the public gRPC API.",
						Value: "0.0.0.0:8081",
					},
					&cli.StringFlag{
						Name:  "admin-http-addr",
						Usage: "Address the admin HTTP server will listen on. Set to - to disable the admin HTTP API.",
						Value: "0.0.0.0:8082",
					},
					&cli.StringFlag{
						Name:  "admin-grpc-addr",
						Usage: "Address the admin gRPC server will listen on. Set to - to disable the admin gRPC HTTP API.",
						Value: "0.0.0.0:8083",
					},
					&cli.StringFlag{
						Name:    "postgres-connection-string",
						Aliases: []string{"p"},
						Usage:   "Postgres connection string",
						Value:   "postgres://transiter:transiter@localhost:5432/transiter",
					},
					&cli.BoolFlag{
						Name:  "read-only",
						Usage: "Run in read only mode (no admin APIs, no scheduler, read only database interactions)",
						Value: false,
					},
					&cli.BoolFlag{
						Name:  "disable-scheduler",
						Usage: "Disable the feed update scheduler",
						Value: false,
					},
					&cli.BoolFlag{
						Name:  "enable-pprof",
						Usage: "Enable pprof debugging via the admin HTTP API",
						Value: true,
					},
					&cli.BoolFlag{
						Name:  "disable-public-metrics",
						Usage: "Don't report Prometheus metrics on the public HTTP API's /metrics endpoint. Metrics are always reported on the admin HTTP API",
						Value: false,
					},
					&cli.Int64Flag{
						Name:  "max-connections",
						Usage: "Maximum size of the Postgres connection pool",
						Value: 50,
					},
					&cli.Int64Flag{
						Name:  "max-stops-per-request",
						Usage: "Maximum number of stops that will be returned in a single list stops request. Specifying a value <= 0 will disable the limit.",
						Value: 100,
					},
					&cli.Int64Flag{
						Name:  "max-vehicles-per-request",
						Usage: "Maximum number of vehicles that will be returned in a single list vehicles request. Specifying a value <= 0 will disable the limit.",
						Value: 100,
					},
					&cli.StringFlag{
						Name:  "log-level",
						Usage: "Log level, either debug, info, warning or error",
						Value: "info",
					},
				},
				Action: func(c *cli.Context) error {
					var logLevel slog.Level
					if err := logLevel.UnmarshalText([]byte(c.String("log-level"))); err != nil {
						return err
					}
					args := server.RunArgs{
						PublicHTTPAddr:        c.String("public-http-addr"),
						PublicGrpcAddr:        c.String("public-grpc-addr"),
						AdminHTTPAddr:         c.String("admin-http-addr"),
						AdminGrpcAddr:         c.String("admin-grpc-addr"),
						PostgresConnStr:       c.String("postgres-connection-string"),
						MaxConnections:        int32(c.Int64("max-connections")),
						DisableScheduler:      c.Bool("disable-scheduler"),
						DisablePublicMetrics:  c.Bool("disable-public-metrics"),
						ReadOnly:              c.Bool("read-only"),
						EnablePprof:           c.Bool("enable-pprof"),
						MaxStopsPerRequest:    int32(c.Int64("max-stops-per-request")),
						MaxVehiclesPerRequest: int32(c.Int64("max-vehicles-per-request")),
						LogLevel:              logLevel,
					}
					ctx, cancel := context.WithCancel(c.Context)
					defer cancel()

					interruptCh := make(chan os.Signal, 1)
					signal.Notify(interruptCh, os.Interrupt)
					defer signal.Stop(interruptCh)

					shutdownCh := make(chan error, 1)
					go func() {
						shutdownCh <- server.Run(ctx, args)
					}()

					var cancelled bool
					for {
						select {
						case <-interruptCh:
							if cancelled {
								return fmt.Errorf("forced an unclean shutdown after receiving second cancellation signal")
							}
							cancelled = true
							cancel()
						case err := <-shutdownCh:
							return err
						}
					}
				},
			},
			{
				Name:  "feed",
				Usage: "perform operations on a data feed",
				Subcommands: []*cli.Command{
					{
						Name:  "update",
						Usage: "perform a feed update",
						Flags: []cli.Flag{
							&cli.BoolFlag{
								Name:  "force",
								Usage: "Perform a full update even if the downloaded data is identical to the last time this feed was updated",
								Value: false,
							},
						},
						Action: func(c *cli.Context) error {
							if c.Args().Len() == 0 {
								return fmt.Errorf("must provide the ID of the feed to update in the form <system_id>/<feed_id>")
							}
							feedAndSystemIds := strings.SplitAfterN(c.Args().Get(0), "/", 2)
							if len(feedAndSystemIds) != 2 {
								return fmt.Errorf("must provide the ID of the feed to update in the form <system_id>/<feed_id>")
							}
							systemID := strings.TrimSuffix(feedAndSystemIds[0], "/")
							feedID := feedAndSystemIds[1]
							if systemID == "" || feedID == "" {
								return fmt.Errorf("must provide the ID of the feed to update in the form <system_id>/<feed_id>")
							}
							return clientAction(func(ctx context.Context, client *client.Client) error {
								return client.UpdateFeed(ctx, systemID, feedID, c.Bool("force"))
							})(c)
						},
					},
					// TODO: pause, unpause, status, etc
				},
			},
			{
				Name:  "version",
				Usage: "print the version of this binary, or a Transiter server",
				Flags: []cli.Flag{
					&cli.BoolFlag{
						Name:  "server",
						Usage: "Print the version of a Transiter server rather than this binary",
						Value: false,
					},
				},
				Action: func(ctx *cli.Context) error {
					if !ctx.Bool("server") {
						fmt.Println(version.Version())
						return nil
					}
					return clientAction(func(ctx context.Context, client *client.Client) error {
						version, err := client.Version(ctx)
						if err != nil {
							return err
						}
						fmt.Println(version)
						return nil
					})(ctx)
				},
			},
		},
	}
	if err := app.Run(os.Args); err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
}

func clientAction(f func(ctx context.Context, client *client.Client) error) func(c *cli.Context) error {
	return func(c *cli.Context) error {
		client, err := client.New(c.String("addr"))
		if err != nil {
			return err
		}
		defer client.Close()
		// TODO: parse the error to remove RPC references
		// For example when a yaml config url provided to install is incorrect
		return f(context.Background(), client)
	}
}
