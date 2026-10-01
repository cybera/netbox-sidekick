#!/usr/bin/env bash
#
# Run the sidekick test suite against a real NetBox instance.
#
# Builds scripts/dev-env/Dockerfile, starts throwaway Postgres and Redis
# containers on a dedicated Docker network, runs the suite, and tears the
# containers down again. Nothing outside those containers is touched.
#
# Usage:
#   scripts/dev-env/run-tests.sh                 # whole suite
#   scripts/dev-env/run-tests.sh sidekick.tests.test_bulk
#
# Requirements: docker, and network access to github.com (NetBox is cloned)
# and pypi.org on the first build.
#
# Note: this only creates and destroys containers named sidekick-test-*.
# It never touches other workloads on the host.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NETWORK=sidekick-test
IMAGE=sidekick-test
PG=sidekick-test-pg
REDIS=sidekick-test-redis

TEST_LABEL="${1:-sidekick}"

cleanup() {
    docker rm -f "$PG" "$REDIS" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== building image (cached after the first run) =="
docker build -q -f "$REPO_ROOT/scripts/dev-env/Dockerfile" -t "$IMAGE" "$REPO_ROOT"

echo "== starting postgres + redis =="
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null
docker run -d --name "$PG" --network "$NETWORK" --network-alias pg \
    -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=netbox postgres:16 >/dev/null
docker run -d --name "$REDIS" --network "$NETWORK" --network-alias redis \
    redis:7-alpine >/dev/null

echo "== running: manage.py test $TEST_LABEL =="
docker run --rm --network "$NETWORK" "$IMAGE" sh -c "
    for i in \$(seq 1 30); do pg_isready -h pg -U postgres >/dev/null 2>&1 && break; sleep 1; done
    python manage.py test $TEST_LABEL -v 2 --noinput
"
