#! /bin/bash

# shellcheck disable=SC2006
CURRENT_VERSION=`grep "version" setup.cfg | awk '{print$3}'`
echo "$CURRENT_VERSION"

# shellcheck disable=SC2006
DOCKER_VERSION_PRESENT=`docker image search --list-tags cebelin/ebel | awk '{print $2}' | grep "$CURRENT_VERSION"`
echo "$DOCKER_VERSION_PRESENT"

if [ ! "$DOCKER_VERSION_PRESENT" ]
then
  echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
  # shellcheck disable=SC2086
  docker build . -t cebelin/ebel:latest -t cebelin/ebel:"$CURRENT_VERSION"
  docker push cebelin/ebel:latest cebelin/ebel:"$CURRENT_VERSION"
fi
