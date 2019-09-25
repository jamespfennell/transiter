#!/usr/bin/env bash

echo "Pushing Docker images to Docker Hub"
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
if ([[ "$TRAVIS_BRANCH" == "master" ]] || [[ ! -z "$TRAVIS_TAG" ]]) && [[ "$TRAVIS_PULL_REQUEST" == "false" ]];
then
    docker push "jamespfennell/transiter:latest-webserver"
    docker push "jamespfennell/transiter:latest-taskserver"
    docker push "jamespfennell/transiter:latest-postgres"
fi;
