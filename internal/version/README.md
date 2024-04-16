# Transiter versioning

Transiter follows [semantic versioning](https://semver.org/).
The base version `X.Y.Z` is stored in the file `BASE_VERSION` in this directory.
The full version then depends on when and where Transiter is built:

- For local builds (i.e., `go build .`) the version is `X.Y.Z-alpha+dev`.

- For non-mainline builds on the GitHub CI, the version is `X.Y.Z-alpha+build<build_number>`.

- For mainline builds on the GitHub CI, the version is `X.Y.Z-beta.<build_number>`.

- For release builds on the GitHub CI, the version is `X.Y.Z`.

To create a new release:

1. Make sure the current mainline HEAD is green.

1. Create a release on GitHub using the tag `vX.Y.Z` where `X.Y.Z` matches exactly
    what is in the file `BASE_VERSION`.

1. Create a new commit on mainline that bumps that patch number in `BASE_VERSION`.
