#!/usr/bin/env bash
#
# TODO: Automate this.
# docker buildx create --name multiarch --use
# docker buildx use multiarch
# docker buildx inspect --bootstrap

DOCKERREPONAME=tmc_audit_streamer
REGISTRYHOST=harbor-repo.vmware.com
REGISTRYPATH=gtt_tap

VERSION=0.0.5
PLATFORMS=linux/amd64,linux/arm64,linux/arm/v7

components=("fluentd" "streamer")

# Iterate over ze two components
for COMPONENT in "${components[@]}"; do
  docker buildx build . \
    --tag $REGISTRYHOST/$REGISTRYPATH/$DOCKERREPONAME:$VERSION-"$COMPONENT" \
    --platform $PLATFORMS \
    --push \
    --file docker/Dockerfile."$COMPONENT"
done
