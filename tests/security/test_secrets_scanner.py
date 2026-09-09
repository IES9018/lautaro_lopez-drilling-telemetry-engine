"""Escaneo estático de secretos hardcodeados en src/ (arnés v3 / RF-12)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

# Extensiones a escanear (código de producción; no node_modules).
_SCAN_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".env", ".yml", ".yaml"}

# Directorios a ignorar.
_SKIP_DIRS = {
    "node_modules",
    ".next",
    "__pycache__",
    ".venv",
    "dist",
    "build",
    "playwright-report",
    "test-results",
    "e2e",  # fixtures E2E no contienen secretos reales
}

# Patrones de credenciales literales.
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "openai_sk",
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
    ),
    (
        "groq_gsk",
        re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    ),
    (
        "anthropic_sk_ant",
        re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}"),
    ),
    (
        "assignment_literal",
        re.compile(
            r"(?i)(api[_-]?key|secret|password|token)\s*=\s*[\"'][^\"']{8,}[\"']"
        ),
    ),
]

# False positives conocidos (nombres de env vars / docs, no valores).
_ALLOWLIST_SUBSTRINGS = (
    "os.environ.get(",
    "process.env.",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "NEXT_PUBLIC_",
    # Comentarios de documentación / nombres de campos
    "bearerFormat",
    "BearerAuth",
)


def _iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in SRC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _SCAN_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def _line_is_allowlisted(line: str) -> bool:
    return any(token in line for token in _ALLOWLIST_SUBSTRINGS)


def test_no_hardcoded_secret_literals_in_src() -> None:
    """Ningún archivo de src/ debe contener claves API o password literales."""
    findings: list[str] = []
    for path in _iter_source_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _line_is_allowlisted(line):
                continue
            # Comentarios de doc que mencionan patrones no cuentan.
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            for name, pattern in _SECRET_PATTERNS:
                if pattern.search(line):
                    rel = path.relative_to(REPO_ROOT)
                    findings.append(f"{rel}:{lineno} [{name}] {line.strip()[:120]}")

    assert findings == [], "Hardcoded secrets found:\n" + "\n".join(findings)


def test_llm_providers_read_keys_from_environ() -> None:
    """Los providers LLM deben leer claves solo vía os.environ.get."""
    diagnostics = SRC_ROOT / "advisor" / "llm_diagnostics.py"
    assert diagnostics.is_file()
    source = diagnostics.read_text(encoding="utf-8")

    for env_name in ("OPENAI_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
        assert f'os.environ.get("{env_name}"' in source, (
            f"{env_name} must be read via os.environ.get in llm_diagnostics.py"
        )
        # No asignación literal del nombre de la variable a un string secreto.
        assert not re.search(
            rf'{env_name}\s*=\s*["\']sk-',
            source,
        )


def test_no_dotenv_committed_with_secrets() -> None:
    """Archivos .env* en la raíz no deben contener valores de secretos."""
    for env_file in REPO_ROOT.glob(".env*"):
        if env_file.name.endswith(".example"):
            continue
        text = env_file.read_text(encoding="utf-8")
        for name, pattern in _SECRET_PATTERNS[:3]:  # solo formatos de claves
            match = pattern.search(text)
            assert match is None, f"{env_file.name} contains {name}: {match.group(0)[:20]}…"


@pytest.mark.parametrize(
    "forbidden",
    [
        "eval(",
        "pickle.loads",
        "pickle.load(",
        "yaml.load(",  # unsafe loader
    ],
)
def test_no_dangerous_deserializers_in_pipeline(forbidden: str) -> None:
    """Pipeline no debe usar eval/pickle sobre telemetría (gobernanza)."""
    pipeline = SRC_ROOT / "pipeline"
    hits: list[str] = []
    for path in pipeline.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if forbidden in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == [], f"Forbidden `{forbidden}` in: {hits}"
