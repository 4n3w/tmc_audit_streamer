#!/usr/bin/env bash
#
# TODO: Automate this. Requires the next two lines
# docker buildx create --name multiarch --use
# docker buildx inspect --bootstrap
#
DOCKERUSER=anwood340
DOCKERREPONAME=tmc_audit_streamer
VERSION=0.0.1
PLATFORMS=linux/amd64,linux/arm64,linux/arm/v7

# Define components as an array
components=("fluentd" "streamer")

# Iterate over ze two components
for COMPONENT in "${components[@]}"; do
  docker buildx build . \
    --tag $DOCKERUSER/$DOCKERREPONAME:$VERSION-"$COMPONENT" \
    --platform $PLATFORMS \
    --push \
    --file docker/Dockerfile."$COMPONENT"
done
