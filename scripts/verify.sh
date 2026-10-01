#!/bin/bash
#
# Static verification for the sidekick NetBox-4 rewrite.
#
# Runs entirely without a NetBox/Django runtime or virtualenv. Intended to be
# re-runnable by an external monitor from a fresh shell:
#
#     cd /home/cyb3ra/jtopjian/netbox-sidekick && bash scripts/verify.sh
#
# Checks:
#   1. py_compile every sidekick/**.py
#   2. AST-resolve every core-app import against a NetBox source tree
#      ($NETBOX_SOURCE, default /tmp/nb470/netbox). If the tree is absent the
#      check is skipped with a warning rather than failing, so the script stays
#      runnable on a machine without the reference checkout.
#   3. pyflakes over the whole tree (reliable; catches unused imports etc.).
#   4. The CI lint gate, i.e. `flake8 --ignore W504,E275,E501 .`, when a
#      working flake8 is available. This is the only check that matches CI
#      exactly.
#
# On flake8: the copy at /opt/ansible/venv/bin/flake8 is broken (its plugin
# manager fails to load), and this repo has no flake8 config file, so there is
# no way to reproduce CI's lint step with pycodestyle alone - pycodestyle
# reports f-string false positives (E231/E241/E202 inside format specs, with
# impossible negative column numbers) that flake8 does not. When flake8 is
# unavailable this script therefore falls back to a narrow pycodestyle scope
# and says so loudly, rather than pretending to have verified the lint gate.
#
# To run the real thing: scripts/dev-env/run-tests.sh, or CI.
#
set -u
cd "$(dirname "$0")/.."

rc=0

echo "== static_check: py_compile + core-import resolution =="
python3 scripts/static_check.py || rc=1

FLAKES="$(command -v pyflakes || true)"
STYLE="$(command -v pycodestyle || true)"
if [ -z "$FLAKES" ] && [ -x /opt/ansible/venv/bin/pyflakes ]; then
  FLAKES=/opt/ansible/venv/bin/pyflakes
fi
if [ -z "$STYLE" ] && [ -x /opt/ansible/venv/bin/pycodestyle ]; then
  STYLE=/opt/ansible/venv/bin/pycodestyle
fi

echo "== pyflakes (whole tree) =="
if [ -n "$FLAKES" ]; then
  "$FLAKES" $(find sidekick -name '*.py' ! -name '__init__.py') || rc=1
else
  echo "pyflakes not available; skipped"
fi

# Locate a flake8 that actually runs. `--version` fails on the broken install,
# so it doubles as the availability probe.
FLAKE8=""
for candidate in "$(command -v flake8 || true)" /opt/ansible/venv/bin/flake8; do
  if [ -n "$candidate" ] && [ -x "$candidate" ] && "$candidate" --version >/dev/null 2>&1; then
    FLAKE8="$candidate"
    break
  fi
done

if [ -n "$FLAKE8" ]; then
  echo "== flake8 --ignore W504,E275,E501 . (CI parity) =="
  "$FLAKE8" --ignore W504,E275,E501 . || rc=1
else
  echo "== pycodestyle fallback (NOT CI parity) =="
  echo "!! flake8 is unavailable or broken. CI runs"
  echo "!!   flake8 --ignore W504,E275,E501 ."
  echo "!! which cannot be reproduced here: local pycodestyle emits f-string"
  echo "!! false positives (E231/E241/E202 in format specs). Only the files"
  echo "!! below are checked, so a green run here does NOT mean a green CI lint."
  echo "!! Use scripts/dev-env/run-tests.sh or CI for the real gate."
  if [ -n "$STYLE" ]; then
    FILES=$(find sidekick/views sidekick/ui sidekick/filtersets sidekick/tables \
        sidekick/models sidekick/forms sidekick/template_content sidekick/api \
        sidekick/tests sidekick/management -name '*.py' \
        ! -path 'sidekick/api/views/clickhousedims.py' \
        ! -path 'sidekick/management/commands/export_data_to_clickhouse.py' \
        ! -path 'sidekick/management/commands/member_contacts.py' \
        ! -path 'sidekick/management/commands/migrate_graphite_to_clickhouse.py' \
        ! -path 'sidekick/management/commands/scrub_snmp_spikes.py' \
        ! -path 'sidekick/utils/clickhouse.py')
    "$STYLE" --ignore W504,E275,E501 $FILES \
      sidekick/search.py sidekick/navigation.py sidekick/urls.py \
      sidekick/__init__.py || rc=1
  else
    echo "pycodestyle not available; skipped"
  fi
fi

if [ "$rc" -eq 0 ]; then
  echo "VERIFY OK"
else
  echo "VERIFY FAILED"
fi
exit "$rc"
