#!/bin/sh
set -e

if [ -n "$GITHUB_PRIVATE_KEY_PEM" ]; then
  printf "$GITHUB_PRIVATE_KEY_PEM" > /tmp/github-app-private-key.pem
  chmod 600 /tmp/github-app-private-key.pem
  export GITHUB_PRIVATE_KEY_PATH=/tmp/github-app-private-key.pem
fi

exec "$@"
