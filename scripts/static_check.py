#!/usr/bin/env python3
"""Static verification for the sidekick NetBox-4 rewrite.

Two checks, neither of which needs a running NetBox/Django:

1. ``py_compile`` every ``.py`` under ``sidekick/`` (syntax).
2. For every absolute import of a NetBox core-app module, resolve the module
   and each imported name against a NetBox source tree (default
   ``/tmp/nb470/netbox``). This catches imports/classes removed in 4.x without
   a database or settings.

Usage:
    python3 scripts/static_check.py [--netbox /path/to/netbox] [--quiet]

Exit code is non-zero if any check fails.
"""
from __future__ import annotations

import argparse
import ast
import os
import py_compile
import sys

CORE_APPS = {
    'netbox', 'utilities', 'extras', 'dcim', 'ipam', 'tenancy', 'users',
    'virtualization', 'circuits', 'vpn', 'wireless', 'core', 'account',
    'extras', 'ipam', 'netbox',
}
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDEKICK = os.path.join(REPO, 'sidekick')


def walk_py(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '__pycache__']
        for fn in filenames:
            if fn.endswith('.py'):
                yield os.path.join(dirpath, fn)


def compile_all():
    errors = []
    count = 0
    for path in walk_py(SIDEKICK):
        count += 1
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(str(exc))
    return count, errors


def _extract_all(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == '__all__':
                    try:
                        value = ast.literal_eval(node.value)
                        if isinstance(value, str):
                            return {value}
                        return set(value)
                    except Exception:
                        return None
    return None


def _module_to_path(netbox_root, module):
    base = os.path.join(netbox_root, *module.split('.'))
    for cand in (base + '.py', os.path.join(base, '__init__.py')):
        if os.path.isfile(cand):
            return cand
    return None


def _module_name(netbox_root, path):
    """Return the dotted module name for a file under netbox_root."""
    rel = os.path.relpath(path, netbox_root)
    if rel.endswith(os.sep + '__init__.py'):
        rel = rel[: -len(os.sep + '__init__.py')]
    elif rel.endswith('.py'):
        rel = rel[:-3]
    return rel.replace(os.sep, '.')


def _resolve_relative(netbox_root, path, level, module):
    """Resolve a relative ImportFrom to an absolute dotted module name."""
    name = _module_name(netbox_root, path)
    is_pkg = path.endswith(os.sep + '__init__.py') or path.endswith('__init__.py')
    pkg = name if is_pkg else name.rsplit('.', 1)[0]
    for _ in range(level - 1):
        pkg = pkg.rsplit('.', 1)[0]
    return pkg + ('.' + module if module else '')


def module_exports(netbox_root, path, seen=None):
    """Best-effort set of names a module exports, following import * ."""
    if seen is None:
        seen = set()
    if path in seen:
        return set()
    seen.add(path)
    try:
        tree = ast.parse(open(path, encoding='utf-8').read())
    except (SyntaxError, OSError):
        return set()

    names = set()
    star_targets = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    names.add(tgt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            if node.level:
                mod = _resolve_relative(netbox_root, path, node.level, mod)
            if any(a.name == '*' for a in node.names):
                tgt = _module_to_path(netbox_root, mod)
                if tgt:
                    star_targets.append(tgt)
            else:
                for alias in node.names:
                    names.add(alias.asname or alias.name)

    for tgt in star_targets:
        names |= module_exports(netbox_root, tgt, seen)

    declared = _extract_all(tree)
    if declared is not None:
        return set(declared)
    return names


def check_imports(netbox_root):
    problems = []
    for path in walk_py(SIDEKICK):
        tree = ast.parse(open(path, encoding='utf-8').read())
        rel = os.path.relpath(path, REPO)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level or not node.module:
                continue
            top = node.module.split('.')[0]
            if top not in CORE_APPS:
                continue
            mod_path = _module_to_path(netbox_root, node.module)
            if mod_path is None:
                problems.append(f"{rel}:{node.lineno}: module '{node.module}' not found in NetBox")
                continue
            exports = module_exports(netbox_root, mod_path)
            for alias in node.names:
                if alias.name == '*':
                    continue
                if alias.name in exports:
                    continue
                # imported name may itself be a submodule
                if _module_to_path(netbox_root, f"{node.module}.{alias.name}"):
                    continue
                problems.append(
                    f"{rel}:{node.lineno}: '{alias.name}' not exported by '{node.module}'"
                )
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--netbox', default=os.environ.get('NETBOX_SOURCE', '/tmp/nb470/netbox'))
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    count, compile_errors = compile_all()
    if not args.quiet:
        print(f"[syntax] compiled {count} files, {len(compile_errors)} errors")
    for e in compile_errors:
        print("  " + e)

    if not os.path.isdir(args.netbox):
        print(f"[imports] NetBox source not found at {args.netbox}; skipping")
        import_problems = []
    else:
        import_problems = check_imports(args.netbox)
        if not args.quiet:
            print(f"[imports] {len(import_problems)} unresolved core imports")
        for p in import_problems:
            print("  " + p)

    if compile_errors or import_problems:
        sys.exit(1)
    if not args.quiet:
        print("OK")
    sys.exit(0)


if __name__ == '__main__':
    main()
