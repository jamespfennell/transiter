- implement the gtfs static parser and import logic
- Async install (and delete?)
- Support for Go templates in the Yaml file
- implement the gtfs realtime parser and import logic
- change serial to bigserial everywhere

- move sqlc and buf config files into subdirectores
- fix lattitude typo
- Right now the GPS lat/long are parsed to and from strings - would be good to avoid conversions
- Rename auto update to periodic update
- Service map group -> service map config
- directionRules -> StopHeadsignRules
- service -> server
- required_for_install -> update_on_update?
- Id -> ID?

- Transit topological sort (Split into components -> transitive reduction -> tree-graph-tree decomposition -> 3 x sort)
