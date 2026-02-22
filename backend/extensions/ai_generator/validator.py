"""Extension code validator — runs BEFORE writing AI-generated files to disk.

Pipeline per .py file:
  1. Python syntax check (ast.parse)
  2. Security scan (no eval/exec, no f-string SQL)
  3. models.py checks (ext_ table prefix, tenant_id present)
  4. routes.py checks (tenant_id filter in queries)

Returns a ValidationResult with errors (blocking) and warnings (informational).
Files are only written to disk if validation passes.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def merge(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.passed:
            self.passed = False

    def __bool__(self) -> bool:
        return self.passed


# ── Syntax ────────────────────────────────────────────────────────────────────

def _check_syntax(filename: str, code: str) -> ValidationResult:
    try:
        ast.parse(code)
        return ValidationResult(passed=True)
    except SyntaxError as e:
        return ValidationResult(
            passed=False,
            errors=[f"**{filename}** line {e.lineno}: {e.msg}"],
        )


# ── Security ──────────────────────────────────────────────────────────────────

_FORBIDDEN_CALLS = ["eval(", "exec(", "compile(", "__import__("]

# Catches SQL built via f-strings: f"SELECT ... WHERE id={...}"
_FSTRING_SQL_RE = re.compile(
    r'f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE|WHERE).*?\{',
    re.IGNORECASE | re.DOTALL,
)


def _check_security(filename: str, code: str) -> ValidationResult:
    errors: list[str] = []
    for call in _FORBIDDEN_CALLS:
        if call in code:
            errors.append(f"**{filename}**: `{call}` is not allowed in extension code")
    if _FSTRING_SQL_RE.search(code):
        errors.append(
            f"**{filename}**: SQL queries must not use f-strings — "
            "use SQLAlchemy expressions instead (SQL injection risk)"
        )
    return ValidationResult(passed=not errors, errors=errors)


# ── models.py ─────────────────────────────────────────────────────────────────

_TABLE_NAME_RE = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')
_MODEL_CLASS_RE = re.compile(r'^class\s+\w+\s*\(Base\)', re.MULTILINE)


def _check_models(filename: str, code: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    has_models = bool(_MODEL_CLASS_RE.search(code))
    if not has_models:
        return ValidationResult(passed=True)

    # All SQLAlchemy tables must start with ext_
    for m in _TABLE_NAME_RE.finditer(code):
        table = m.group(1)
        if not table.startswith("ext_"):
            errors.append(
                f"**{filename}**: table `{table}` must start with `ext_` "
                "(e.g. `ext_my_extension_items`)"
            )

    # Every model table must have tenant_id (data isolation)
    if "tenant_id" not in code:
        errors.append(
            f"**{filename}**: models must include a `tenant_id` column "
            "(required for multi-tenant data isolation)"
        )

    # Soft warning for missing created_by
    if "created_by" not in code:
        warnings.append(
            f"**{filename}**: models should include `created_by` (UUID of the creating user)"
        )

    return ValidationResult(passed=not errors, errors=errors, warnings=warnings)


# ── routes.py ─────────────────────────────────────────────────────────────────

def _check_routes(filename: str, code: str) -> ValidationResult:
    warnings: list[str] = []

    # If there are SQLAlchemy select() calls, tenant_id should appear in the query
    if "select(" in code and "tenant_id" not in code:
        warnings.append(
            f"**{filename}**: queries may be missing `tenant_id` filter — "
            "ensure every query filters by `current_user.tenant_id`"
        )

    return ValidationResult(passed=True, warnings=warnings)


# ── extension.py ──────────────────────────────────────────────────────────────

_EXT_NAME_RE = re.compile(r'name\s*=\s*["\']([a-z][a-z0-9_]*)["\']')
_API_PREFIX_RE = re.compile(r'api_prefix\s*=\s*["\']([^"\']+)["\']')


def _check_extension(filename: str, code: str) -> ValidationResult:
    warnings: list[str] = []

    if "ExtensionBase)" not in code:
        return ValidationResult(
            passed=False,
            errors=[f"**{filename}**: extension class must inherit from `ExtensionBase`"]
        )

    # name must be snake_case
    m = _EXT_NAME_RE.search(code)
    if m:
        name = m.group(1)
        if not re.match(r'^[a-z][a-z0-9_]+$', name):
            warnings.append(
                f"**{filename}**: extension name `{name}` should be snake_case (e.g. `my_extension`)"
            )

    # api_prefix must start with /
    m2 = _API_PREFIX_RE.search(code)
    if m2:
        prefix = m2.group(1)
        if not prefix.startswith("/"):
            warnings.append(
                f"**{filename}**: api_prefix `{prefix}` must start with `/`"
            )

    return ValidationResult(passed=True, warnings=warnings)


# ── Entry point ───────────────────────────────────────────────────────────────

def validate_files(files: dict[str, str]) -> ValidationResult:
    """Validate all AI-generated extension files.

    Args:
        files: mapping of relative path → file content

    Returns:
        ValidationResult (passed=True iff no errors)
    """
    combined = ValidationResult(passed=True)

    for path, content in files.items():
        if not path.endswith(".py"):
            continue

        filename = Path(path).name

        # 1. Syntax — stop further checks for this file if broken
        syntax = _check_syntax(filename, content)
        combined.merge(syntax)
        if not syntax.passed:
            continue

        # 2. Security — applies to all .py files
        combined.merge(_check_security(filename, content))

        # 3. File-type-specific
        if filename == "models.py":
            combined.merge(_check_models(filename, content))
        elif filename == "routes.py":
            combined.merge(_check_routes(filename, content))
        elif filename == "extension.py":
            combined.merge(_check_extension(filename, content))

    return combined
