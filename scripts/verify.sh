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
#   3. pyflakes (non-__init__ modules) and pycodestyle, if available.
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

echo "== pyflakes =="
if [ -n "$FLAKES" ]; then
  "$FLAKES" $(find sidekick -name '*.py' ! -name '__init__.py') || rc=1
else
  echo "pyflakes not available; skipped"
fi

echo "== pycodestyle (ignoring W504,E275,E501) =="
if [ -n "$STYLE" ]; then
  # Only the files this rewrite touched. Pre-existing violations in management
  # commands / utils are out of scope, as is the known pycodestyle false
  # positive on the f-string semicolon in api/views/clickhousedims.py:55.
  FILES=$(find sidekick/views sidekick/ui sidekick/filtersets sidekick/tables \
      sidekick/models sidekick/forms sidekick/template_content sidekick/api \
      sidekick/tests -name '*.py' ! -path 'sidekick/api/views/clickhousedims.py')
  "$STYLE" --ignore W504,E275,E501 $FILES \
    sidekick/search.py sidekick/navigation.py sidekick/urls.py \
    sidekick/__init__.py || rc=1
else
  echo "pycodestyle not available; skipped"
fi

if [ "$rc" -eq 0 ]; then
  echo "VERIFY OK"
else
  echo "VERIFY FAILED"
fi
exit "$rc"
