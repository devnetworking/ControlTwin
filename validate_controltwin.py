#!/usr/bin/env python3
"""
validate_controltwin.py

Validate ControlTwin project structure across:
- controltwin-backend
- controltwin-frontend
- controltwin-ai

Features:
- Critical/optional file existence checks
- File content validations by extension
- Python syntax checks via ast.parse
- JSON/YAML parsing checks
- Quality/stub warnings
- Color-coded report (✅ / ❌ / ⚠️ / ℹ️)
- JSON report export for CI/CD
- Optional stub generation for missing critical .py/.js/.jsx files

Python: 3.8+
Dependencies: none required
Optional dependencies:
- colorama (for better Windows color support)
- pyyaml (for YAML validation)
"""

import argparse
import ast
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Optional color support
COLORAMA_AVAILABLE = False
try:
    from colorama import init as colorama_init  # type: ignore
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except Exception:
    COLORAMA_AVAILABLE = False

# Optional YAML support
# NOTE: Some environments may have a broken PyYAML install that can hang/fail at import.
# To keep this validator robust and dependency-optional, YAML validation is disabled by default.
# Enable by setting CONTROLTWIN_ENABLE_YAML=1 in environment.
YAML_AVAILABLE = False
yaml = None  # type: ignore
if os.environ.get("CONTROLTWIN_ENABLE_YAML", "0") == "1":
    try:
        import yaml as _yaml  # type: ignore
        yaml = _yaml  # type: ignore
        YAML_AVAILABLE = True
    except Exception:
        YAML_AVAILABLE = False


class Colors:
    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"

    @staticmethod
    def colorize(text: str, color: str) -> str:
        # If ANSI is not supported, return plain text
        # colorama can help on Windows; if absent, still print symbols.
        if COLORAMA_AVAILABLE or os.name != "nt":
            return f"{color}{text}{Colors.RESET}"
        return text


SYMBOL_OK = "✅"
SYMBOL_FAIL = "❌"
SYMBOL_WARN = "⚠️"
SYMBOL_INFO = "ℹ️"


def info(msg: str) -> str:
    return Colors.colorize(f"{SYMBOL_INFO} {msg}", Colors.CYAN)


def ok(msg: str) -> str:
    return Colors.colorize(f"{SYMBOL_OK} {msg}", Colors.GREEN)


def fail(msg: str) -> str:
    return Colors.colorize(f"{SYMBOL_FAIL} {msg}", Colors.RED)


def warn(msg: str) -> str:
    return Colors.colorize(f"{SYMBOL_WARN} {msg}", Colors.YELLOW)


def get_git_hash(root: Path) -> Optional[str]:
    git_dir = root / ".git"
    if not git_dir.exists():
        return None
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        return None
    return None


def count_lines(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def safe_read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return None
    except Exception:
        return None


def create_python_stub(path: Path) -> None:
    module_name = path.stem
    content = f'''"""
Auto-generated stub for missing critical module: {module_name}
TODO: Implement module logic.
"""

# TODO: implement {module_name}


def placeholder():
    """
    Placeholder function for initial importability.
    """
    return None
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_component_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    parts = re.split(r"[^A-Za-z0-9]+", stem)
    name = "".join(p[:1].upper() + p[1:] for p in parts if p)
    if not name:
        name = "GeneratedComponent"
    if not re.match(r"[A-Za-z_]", name):
        name = f"C{name}"
    return name


def create_jsx_stub(path: Path) -> None:
    component_name = make_component_name_from_filename(path.name)
    content = f"""import React from "react";

/**
 * Auto-generated stub for missing critical component/file.
 * TODO: Implement {component_name}
 */
export default function {component_name}() {{
  return (
    <div>
      <h2>{component_name}</h2>
      <p>TODO: Implement component.</p>
    </div>
  );
}}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_file_content(path: Path) -> Dict[str, Any]:
    """
    Returns:
    {
      "status": "valid"|"error"|"warning"|"skipped",
      "line_count": int,
      "issues": [str, ...]
    }
    """
    result = {
        "status": "valid",
        "line_count": 0,
        "issues": [],
    }

    text = safe_read_text(path)
    if text is None:
        result["status"] = "error"
        result["issues"].append("Unreadable file (encoding or IO error).")
        return result

    lc = count_lines(text)
    result["line_count"] = lc
    suffix = path.suffix.lower()

    # Generic emptiness checks for some types
    if suffix in {".sql", ".sh", ".md", ".js", ".jsx", ".py", ".json", ".yml", ".yaml", ".html"}:
        if lc == 0:
            result["status"] = "error"
            result["issues"].append("File is empty.")

    # .py checks
    if suffix == ".py":
        # syntax
        try:
            ast.parse(text)
        except SyntaxError as e:
            result["status"] = "error"
            result["issues"].append(f"Python syntax error: {e}")

        # quality warnings
        if lc < 20:
            if result["status"] != "error":
                result["status"] = "warning"
            result["issues"].append("Python file has < 20 lines (possible stub).")

        lowered = text.lower()
        if "pass  # TODO" in text or "raise NotImplementedError" in text:
            if result["status"] != "error":
                result["status"] = "warning"
            result["issues"].append("Contains TODO/NotImplemented stub markers.")

        if "placeholder" in lowered:
            if result["status"] != "error":
                result["status"] = "warning"
            result["issues"].append('Contains "placeholder" text.')

    # .js / .jsx checks
    elif suffix in {".js", ".jsx"}:
        if lc <= 10:
            result["status"] = "error"
            result["issues"].append("JS/JSX file must be non-empty (>10 lines).")

        todo_count = len(re.findall(r"//\s*TODO", text))
        lowered = text.lower()

        if lc < 30:
            if result["status"] != "error":
                result["status"] = "warning"
            result["issues"].append("JS/JSX file has < 30 lines (possible stub).")

        if todo_count > 3:
            if result["status"] != "error":
                result["status"] = "warning"
            result["issues"].append("Contains more than 3 // TODO placeholders.")

        if "placeholder" in lowered or "lorem ipsum" in lowered:
            if result["status"] != "error":
                result["status"] = "warning"
            result["issues"].append('Contains "placeholder" or "lorem ipsum".')

    # .json checks
    elif suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            result["status"] = "error"
            result["issues"].append(f"Invalid JSON: {e}")

    # .yml/.yaml checks
    elif suffix in {".yml", ".yaml"}:
        if YAML_AVAILABLE:
            try:
                yaml.safe_load(text)  # type: ignore
            except Exception as e:
                result["status"] = "error"
                result["issues"].append(f"Invalid YAML: {e}")
        else:
            if result["status"] == "valid":
                result["status"] = "warning"
            result["issues"].append("PyYAML not installed; YAML validation skipped.")

    # .html checks
    elif suffix == ".html":
        if "<!DOCTYPE html>" not in text:
            result["status"] = "error"
            result["issues"].append("Missing <!DOCTYPE html> declaration.")

    # .md checks
    elif suffix == ".md":
        if lc <= 5:
            result["status"] = "warning"
            result["issues"].append("Markdown file has <= 5 lines.")

    # .sh checks
    elif suffix == ".sh":
        if lc == 0:
            result["status"] = "error"
            result["issues"].append("Shell script is empty.")
        else:
            first_line = text.splitlines()[0].strip() if lc > 0 else ""
            if first_line not in {"#!/bin/bash", "#!/bin/sh"}:
                result["status"] = "warning"
                result["issues"].append("Missing shebang #!/bin/bash or #!/bin/sh.")

    # .sql checks
    elif suffix == ".sql":
        if lc == 0:
            result["status"] = "error"
            result["issues"].append("SQL file is empty.")

    return result


def build_project_specs() -> Dict[str, Dict[str, Any]]:
    return {
        "controltwin-backend": {
            "critical": [
                "app/__init__.py",
                "app/main.py",
                "app/core/config.py",
                "app/core/security.py",
                "app/core/logging.py",
                "app/models/__init__.py",
                "app/models/models.py",
                "app/schemas/schemas.py",
                "app/auth/dependencies.py",
                "app/auth/rbac.py",
                "app/db/postgres.py",
                "app/db/influxdb.py",
                "app/services/user_service.py",
                "app/services/asset_service.py",
                "app/services/alert_service.py",
                "app/services/kafka_service.py",
                "app/collectors/modbus_collector.py",
                "app/collectors/opcua_collector.py",
                "app/api/v1/router.py",
                "app/api/v1/endpoints/auth.py",
                "app/api/v1/endpoints/users.py",
                "app/api/v1/endpoints/sites.py",
                "app/api/v1/endpoints/assets.py",
                "app/api/v1/endpoints/datapoints.py",
                "app/api/v1/endpoints/alerts.py",
                "app/api/v1/endpoints/collectors.py",
                "app/api/v1/endpoints/health.py",
                "docker-compose.yml",
                "docker/Dockerfile",
                "docker/postgres/init.sql",
                "requirements.txt",
                ".env.example",
            ],
            "optional": [
                "tests/test_backend.py",
                "README.md",
                "alembic.ini",
                "alembic/env.py",
            ],
        },
        "controltwin-frontend": {
            "critical": [
                "src/main.jsx",
                "src/App.jsx",
                "src/index.css",
                "src/lib/axios.js",
                "src/lib/queryClient.js",
                "src/lib/utils.js",
                "src/store/authStore.js",
                "src/store/alertStore.js",
                "src/api/auth.js",
                "src/api/sites.js",
                "src/api/assets.js",
                "src/api/datapoints.js",
                "src/api/alerts.js",
                "src/api/collectors.js",
                "src/hooks/useAuth.js",
                "src/hooks/useAlerts.js",
                "src/hooks/useAssets.js",
                "src/hooks/useTimeseries.js",
                "src/hooks/useSiteContext.js",
                "src/components/layout/AppLayout.jsx",
                "src/components/layout/Sidebar.jsx",
                "src/components/layout/TopBar.jsx",
                "src/components/ui/StatusDot.jsx",
                "src/components/ui/SeverityBadge.jsx",
                "src/components/ui/MetricCard.jsx",
                "src/components/ui/LoadingSpinner.jsx",
                "src/components/ui/EmptyState.jsx",
                "src/components/charts/TimeSeriesChart.jsx",
                "src/components/charts/AlertBarChart.jsx",
                "src/components/topology/ICSTopology.jsx",
                "src/components/alerts/AlertTable.jsx",
                "src/components/alerts/AlertDetailDrawer.jsx",
                "src/pages/LoginPage.jsx",
                "src/pages/DashboardPage.jsx",
                "src/pages/AssetsPage.jsx",
                "src/pages/AssetDetailPage.jsx",
                "src/pages/TopologyPage.jsx",
                "src/pages/AlertsPage.jsx",
                "src/pages/CollectorsPage.jsx",
                "src/pages/UsersPage.jsx",
                "src/constants/ics.js",
                "src/router/ProtectedRoute.jsx",
                "index.html",
                "vite.config.js",
                "tailwind.config.js",
                "postcss.config.js",
                "package.json",
            ],
            "optional": [
                "components.json",
                ".env.example",
                "README.md",
                "public/favicon.svg",
            ],
        },
        "controltwin-ai": {
            "critical": [
                "app/main.py",
                "app/core/config.py",
                "app/core/logging.py",
                "app/twin_state/engine.py",
                "app/twin_state/reconciler.py",
                "app/twin_state/models.py",
                "app/anomaly/detector.py",
                "app/anomaly/isolation_forest.py",
                "app/anomaly/lstm_autoencoder.py",
                "app/anomaly/baseline.py",
                "app/anomaly/mitre_mapper.py",
                "app/predictive/predictor.py",
                "app/predictive/features.py",
                "app/predictive/scheduler.py",
                "app/remediation/engine.py",
                "app/remediation/rag.py",
                "app/remediation/knowledge_base/indexer.py",
                "app/remediation/knowledge_base/mitre_ics.py",
                "app/simulation/simulator.py",
                "app/simulation/scenario_generator.py",
                "app/simulation/physical_models.py",
                "app/workers/kafka_consumer.py",
                "app/workers/celery_app.py",
                "app/api/router.py",
                "app/api/twin_state.py",
                "app/api/anomaly.py",
                "app/api/predictive.py",
                "app/api/remediation.py",
                "app/api/simulation.py",
                "docker-compose.ai.yml",
                "docker/Dockerfile.ai",
                "docker/ollama/init.sh",
                "requirements-ai.txt",
                ".env.example",
            ],
            "optional": [
                "tests/test_twin_state.py",
                "tests/test_anomaly.py",
                "tests/test_remediation.py",
                "tests/test_physical_models.py",
                "README.md",
            ],
        },
    }


def should_skip(project_name: str, args: argparse.Namespace) -> bool:
    if project_name == "controltwin-backend" and args.skip_backend:
        return True
    if project_name == "controltwin-frontend" and args.skip_frontend:
        return True
    if project_name == "controltwin-ai" and args.skip_ai:
        return True
    return False


def validate_project(
    root: Path,
    project_name: str,
    spec: Dict[str, List[str]],
    fix_missing: bool = False,
) -> Dict[str, Any]:
    project_dir = root / project_name

    report: Dict[str, Any] = {
        "project": project_name,
        "exists": project_dir.exists(),
        "critical_total": len(spec["critical"]),
        "critical_present": 0,
        "optional_total": len(spec["optional"]),
        "optional_present": 0,
        "critical_missing": [],
        "optional_missing": [],
        "syntax_errors": 0,
        "quality_warnings": 0,
        "validation_errors": 0,
        "stubs_created": [],
        "per_file_details": [],
    }

    if not project_dir.exists():
        # All files missing if project dir doesn't exist.
        report["critical_missing"] = list(spec["critical"])
        report["optional_missing"] = list(spec["optional"])
        for rel in spec["critical"]:
            report["per_file_details"].append(
                {
                    "path": str(Path(project_name) / rel),
                    "required": "critical",
                    "status": "missing",
                    "line_count": 0,
                    "issues": ["Project directory missing."],
                }
            )
        for rel in spec["optional"]:
            report["per_file_details"].append(
                {
                    "path": str(Path(project_name) / rel),
                    "required": "optional",
                    "status": "missing",
                    "line_count": 0,
                    "issues": ["Project directory missing."],
                }
            )
        return report

    # Check critical files
    for rel in spec["critical"]:
        full = project_dir / rel
        detail = {
            "path": str(Path(project_name) / rel),
            "required": "critical",
            "status": "",
            "line_count": 0,
            "issues": [],
        }

        if full.exists():
            report["critical_present"] += 1
            v = validate_file_content(full)
            detail["line_count"] = v["line_count"]
            detail["issues"] = v["issues"]

            if v["status"] == "error":
                detail["status"] = "error"
                report["validation_errors"] += 1
                # classify syntax errors for .py parse failures
                if any("Python syntax error" in i for i in v["issues"]):
                    report["syntax_errors"] += 1
            elif v["status"] == "warning":
                detail["status"] = "warning"
                report["quality_warnings"] += 1
            else:
                detail["status"] = "ok"
        else:
            detail["status"] = "missing"
            detail["issues"] = ["Critical file missing."]
            report["critical_missing"].append(rel)

            # --fix-missing behavior for critical Python/JS/JSX
            if fix_missing and full.suffix.lower() in {".py", ".js", ".jsx"}:
                try:
                    if full.suffix.lower() == ".py":
                        create_python_stub(full)
                    else:
                        create_jsx_stub(full)
                    report["stubs_created"].append(str(Path(project_name) / rel))
                    # Re-validate after creation
                    if full.exists():
                        report["critical_present"] += 1
                        report["critical_missing"].pop()  # remove just-added missing
                        v = validate_file_content(full)
                        detail["status"] = "fixed_stub"
                        detail["line_count"] = v["line_count"]
                        detail["issues"] = ["Stub auto-created via --fix-missing"] + v["issues"]
                        if v["status"] == "error":
                            report["validation_errors"] += 1
                            if any("Python syntax error" in i for i in v["issues"]):
                                report["syntax_errors"] += 1
                        elif v["status"] == "warning":
                            report["quality_warnings"] += 1
                except Exception as e:
                    detail["issues"].append(f"Failed to create stub: {e}")

        report["per_file_details"].append(detail)

    # Check optional files
    for rel in spec["optional"]:
        full = project_dir / rel
        detail = {
            "path": str(Path(project_name) / rel),
            "required": "optional",
            "status": "",
            "line_count": 0,
            "issues": [],
        }

        if full.exists():
            report["optional_present"] += 1
            v = validate_file_content(full)
            detail["line_count"] = v["line_count"]
            detail["issues"] = v["issues"]
            if v["status"] == "error":
                detail["status"] = "error"
                report["validation_errors"] += 1
                if any("Python syntax error" in i for i in v["issues"]):
                    report["syntax_errors"] += 1
            elif v["status"] == "warning":
                detail["status"] = "warning"
                report["quality_warnings"] += 1
            else:
                detail["status"] = "ok"
        else:
            detail["status"] = "missing_optional"
            detail["issues"] = ["Optional file missing."]
            report["optional_missing"].append(rel)

        report["per_file_details"].append(detail)

    return report


def print_project_report(project_report: Dict[str, Any]) -> None:
    project = project_report["project"]
    print(info(f"Validating {project}"))

    for f in project_report["per_file_details"]:
        status = f["status"]
        path = f["path"]
        issues = f.get("issues", [])
        line_count = f.get("line_count", 0)
        required = f.get("required", "unknown")

        if status in {"ok"}:
            print(ok(f"[{required}] {path} (lines: {line_count})"))
        elif status in {"fixed_stub"}:
            print(warn(f"[{required}] {path} (stub created, lines: {line_count})"))
            for issue in issues:
                print(warn(f"    - {issue}"))
        elif status in {"warning"}:
            print(warn(f"[{required}] {path} (lines: {line_count})"))
            for issue in issues:
                print(warn(f"    - {issue}"))
        elif status in {"missing"}:
            print(fail(f"[{required}] {path}"))
            for issue in issues:
                print(fail(f"    - {issue}"))
        elif status in {"missing_optional"}:
            print(warn(f"[{required}] {path}"))
            for issue in issues:
                print(warn(f"    - {issue}"))
        elif status in {"error"}:
            print(fail(f"[{required}] {path} (lines: {line_count})"))
            for issue in issues:
                print(fail(f"    - {issue}"))
        else:
            print(info(f"[{required}] {path} (status: {status})"))

    if project_report["stubs_created"]:
        print(info("Stubs created:"))
        for s in project_report["stubs_created"]:
            print(warn(f"  - {s}"))

    print("")


def print_summary(overall: Dict[str, Any], strict: bool = False) -> None:
    print("═══════════════════════════════════════════════════")
    print("  CONTROLTWIN VALIDATION REPORT")
    print("═══════════════════════════════════════════════════")

    for line in overall["project_lines"]:
        print(f"  {line}")

    print("───────────────────────────────────────────────────")

    critical_missing = overall["critical_missing"]
    optional_missing = overall["optional_missing"]
    syntax_errors = overall["syntax_errors"]
    quality_warnings = overall["quality_warnings"]

    cm_text = f"  CRITICAL missing : {critical_missing} files"
    om_text = f"  Optional missing : {optional_missing} files"
    se_text = f"  Syntax errors    : {syntax_errors} files"
    qw_text = f"  Quality warnings : {quality_warnings} files"

    if critical_missing > 0:
        print(Colors.colorize(cm_text, Colors.RED))
    else:
        print(cm_text)

    print(Colors.colorize(om_text, Colors.YELLOW) if optional_missing > 0 else om_text)
    print(Colors.colorize(se_text, Colors.RED) if syntax_errors > 0 else se_text)
    print(Colors.colorize(qw_text, Colors.YELLOW) if quality_warnings > 0 else qw_text)

    print("───────────────────────────────────────────────────")

    fail_due_to_strict = strict and quality_warnings > 0
    incomplete = critical_missing > 0 or syntax_errors > 0 or fail_due_to_strict
    if incomplete:
        print(Colors.colorize("  OVERALL STATUS: ❌ INCOMPLETE", Colors.RED))
    else:
        print(Colors.colorize("  OVERALL STATUS: ✅ READY", Colors.GREEN))

    print("═══════════════════════════════════════════════════")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ControlTwin project structure and file quality."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory containing controltwin-backend/controltwin-frontend/controltwin-ai",
    )
    parser.add_argument(
        "--fix-missing",
        action="store_true",
        help="Create stubs for missing critical Python/JS/JSX files.",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Output format: text (default) or json.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat quality warnings as errors (exit code 1).",
    )
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend validation.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend validation.")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI validation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    specs = build_project_specs()

    timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    git_hash = get_git_hash(root)

    overall_report: Dict[str, Any] = {
        "timestamp": timestamp,
        "git_hash": git_hash,
        "root": str(root),
        "projects": {},
        "critical_missing": 0,
        "optional_missing": 0,
        "syntax_errors": 0,
        "quality_warnings": 0,
        "validation_errors": 0,
        "stubs_created": [],
        "project_lines": [],
        "per_file_details": [],
    }

    for project_name, spec in specs.items():
        if should_skip(project_name, args):
            continue

        project_report = validate_project(
            root=root,
            project_name=project_name,
            spec=spec,
            fix_missing=args.fix_missing,
        )
        overall_report["projects"][project_name] = project_report

        if args.report == "text":
            print_project_report(project_report)

        overall_report["critical_missing"] += len(project_report["critical_missing"])
        overall_report["optional_missing"] += len(project_report["optional_missing"])
        overall_report["syntax_errors"] += project_report["syntax_errors"]
        overall_report["quality_warnings"] += project_report["quality_warnings"]
        overall_report["validation_errors"] += project_report["validation_errors"]
        overall_report["stubs_created"].extend(project_report["stubs_created"])
        overall_report["per_file_details"].extend(project_report["per_file_details"])

        line = (
            f"{project_name:<20}: "
            f"{project_report['critical_present']:02d}/{project_report['critical_total']:02d} critical  |  "
            f"{project_report['optional_present']:02d}/{project_report['optional_total']:02d} optional"
        )
        overall_report["project_lines"].append(line)

    # JSON report output
    if args.report == "json":
        output = {
            "timestamp": overall_report["timestamp"],
            "git_hash": overall_report["git_hash"],
            "root": overall_report["root"],
            "summary": {
                "critical_missing": overall_report["critical_missing"],
                "optional_missing": overall_report["optional_missing"],
                "syntax_errors": overall_report["syntax_errors"],
                "quality_warnings": overall_report["quality_warnings"],
                "validation_errors": overall_report["validation_errors"],
                "strict_mode": args.strict,
            },
            "projects": overall_report["projects"],
            "per_file_details": overall_report["per_file_details"],
            "stubs_created": overall_report["stubs_created"],
        }
        out_path = root / "validation_report.json"
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        # Also print concise text summary to terminal
        print(info(f"JSON report written to: {out_path}"))

    # Always print summary in text mode; in json mode print concise summary too.
    print_summary(overall_report, strict=args.strict)

    # Exit rules:
    # - Exit 1 if any CRITICAL file missing
    # - Exit 1 if syntax errors > 0
    # - Exit 1 if strict and quality warnings > 0
    # - else 0
    if overall_report["critical_missing"] > 0:
        return 1
    if overall_report["syntax_errors"] > 0:
        return 1
    if args.strict and overall_report["quality_warnings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
