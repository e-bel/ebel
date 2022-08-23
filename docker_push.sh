#! /bin/bash

# shellcheck disable=SC2006
CURRENT_VERSION=`grep "version" setup.cfg | awk '{print$3}'`
echo "$CURRENT_VERSION"

# shellcheck disable=SC2006
DOCKER_VERSION_PRESENT=`curl -s -S "https://registry.hub.docker.com/v2/repositories/cebelin/ebel/tags/" | \
  sed -e 's/,/,\n/g' -e 's/\[/\[\n/g' | \
  grep '"name"' | \
  awk -F\" '{print $4;}' | \
  sort -fu | \
  grep "$CURRENT_VERSION"`
echo "$DOCKER_VERSION_PRESENT"

if [ ! "$DOCKER_VERSION_PRESENT" ]
then
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  # shellcheck disable=SC2086
  docker build . -t cebelin/ebel:latest -t cebelin/ebel:"$CURRENT_VERSION"
  docker image push cebelin/ebel:latest
  docker image push cebelin/ebel:"$CURRENT_VERSION"
#  docker pushrm cebelin/ebel
fi
