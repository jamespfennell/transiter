Blocking the merge to mainline:

- change serial to bigserial everywhere
- Right now the GPS lat/long are parsed to and from strings - would be good to avoid conversions
- Remove the /admin prefix (or have an option to it)
- Figure out the home of the config package.

Not blocking the merge to mainline:

- move sqlc and buf config files into subdirectores
- Async install (and delete?)
- Transit topological sort (Split into components -> transitive reduction -> tree-graph-tree decomposition -> 3 x sort)
- Add new index on service map vertex
- Support GPS search
