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
#
# Speed: the NetBox test database is migrated once (~5.5 min from scratch)
# and then reused. Postgres data lives in a named volume that cleanup()
# deliberately does NOT delete, and the test run passes --keepdb, so
# subsequent runs skip the migration entirely. RESET=1 deletes the volume
# for a from-scratch run (e.g. after a Postgres major version bump).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NETWORK=sidekick-test
IMAGE=sidekick-test
PG=sidekick-test-pg
REDIS=sidekick-test-redis
PGDATA=sidekick-test-pgdata

TEST_LABEL="${1:-sidekick}"

cleanup() {
    docker rm -f "$PG" "$REDIS" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
    # The volume is intentionally kept across runs (see the Speed note);
    # only RESET=1 deletes it.
    if [[ "${RESET:-0}" == 1 ]]; then
        docker volume rm "$PGDATA" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

echo "== building image (cached after the first run) =="
docker build -q -f "$REPO_ROOT/scripts/dev-env/Dockerfile" -t "$IMAGE" "$REPO_ROOT"

echo "== starting postgres + redis =="
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null
docker run -d --name "$PG" --network "$NETWORK" --network-alias pg \
    -v "$PGDATA":/var/lib/postgresql/data \
    -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=netbox postgres:16 >/dev/null
docker run -d --name "$REDIS" --network "$NETWORK" --network-alias redis \
    redis:7-alpine >/dev/null

echo "== running: manage.py test $TEST_LABEL =="
docker run --rm --network "$NETWORK" "$IMAGE" sh -c "
    for i in \$(seq 1 30); do pg_isready -h pg -U postgres >/dev/null 2>&1 && break; sleep 1; done
    python manage.py test $TEST_LABEL -v 2 --noinput --keepdb
"
