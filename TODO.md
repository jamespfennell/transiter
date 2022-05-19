
- Parse direction rules
- Parse vehicle
- implement the gtfs static parser and import logic
- Async install (and delete?)
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
- Can we configure the /admin prefix non-statically? Yeah, we just have to add HTTP middleware
- Transit topological sort (Split into components -> transitive reduction -> tree-graph-tree decomposition -> 3 x sort)
