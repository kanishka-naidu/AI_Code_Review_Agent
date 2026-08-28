"""Python quality analyzer using configured Ruff, Radon, and AST thresholds."""
from __future__ import annotations

import ast
import json
from typing import Any

from app.analyzers.base.analyzer import Analyzer
from app.analyzers.common.tooling import (
    AnalyzerError,
    build_finding,
    get_python_executable,
    render_command_options,
    run_command,
    severity_from_config,
    write_temp_source,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.models.finding import Finding
from app.models.severity import Severity

logger = get_logger(__name__)


class PythonQualityAnalyzer(Analyzer):
    name = "python_quality"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._analysis_config = get_repository_config().load("analysis.json")
        self._severity_config = get_repository_config().load("severity.json")
        self._analyzer_config = get_repository_config().load("analyzers.json")
        self._quality_config = self._analyzer_config.get("python_quality", {})
        self._ast_tool = str(self._analyzer_config.get("tool_modules", {}).get("python_ast"))

    def analyze(self, source: str, filename: str) -> tuple[list[Finding], dict[str, Any]]:
        """Run configured Python quality checks."""
        logger.info("PythonQualityAnalyzer started for '%s'", filename)
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return [
                build_finding(
                    rule_id=str(self._analysis_config.get("syntax_error_rule")),
                    title=str(exc.msg),
                    description=str(exc),
                    severity=severity_from_config("high"),
                    category=str(self._analysis_config.get("quality_category")),
                    line=exc.lineno,
                    evidence=str(exc.text or "").strip(),
                    tool_source=self._ast_tool,
                )
            ], {}

        default_name = str(self._analysis_config.get("python_default_filename"))
        temp_path = write_temp_source(source, filename or default_name)
        python = get_python_executable()
        findings = (
            self._run_ruff(python, temp_path)
            + self._run_radon_cc(python, temp_path)
            + self._run_radon_mi(python, temp_path)
            + self._ast_checks(tree)
        )
        logger.info("PythonQualityAnalyzer finished for '%s' with %d findings", filename, len(findings))
        return findings, {}

    def _run_ruff(self, python: str, temp_path: Any) -> list[Finding]:
        module = str(self._analyzer_config.get("tool_modules", {}).get("ruff"))
        ruff_options_str = self._settings.ruff_options or self._analyzer_config.get("tool_options", {}).get("ruff", "")
        options = render_command_options(
            self._settings.csv_list(ruff_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent)},
        )
        try:
            output = run_command([python, "-m", module, *options], cwd=str(temp_path.parent), timeout=self._settings.analyzer_timeout)
            issues = json.loads(output or "[]")
        except (AnalyzerError, json.JSONDecodeError) as exc:
            logger.error("Ruff failed or returned invalid output: %s", exc)
            return []

        prefix_map = self._severity_config.get("ruff_prefix", {})
        findings: list[Finding] = []
        for issue in issues:
            rule_id = issue.get("code") or module
            message = issue.get("message") or rule_id
            loc = issue.get("location") or {}
            raw_level = str(rule_id)[:1]
            configured_sev = prefix_map.get(raw_level, prefix_map.get("default"))
            findings.append(
                build_finding(
                    rule_id=str(rule_id),
                    title=str(message),
                    description=str(message),
                    severity=severity_from_config(configured_sev),
                    category=str(self._analysis_config.get("quality_category")),
                    line=loc.get("row"),
                    column=loc.get("column"),
                    evidence=issue.get("fix", {}).get("message") if issue.get("fix") else message,
                    tool_source=module,
                    finding_metadata={"url": issue.get("url"), "fix": issue.get("fix")},
                )
            )
        return findings

    def _run_radon_cc(self, python: str, temp_path: Any) -> list[Finding]:
        module = str(self._analyzer_config.get("tool_modules", {}).get("radon"))
        radon_cc_options_str = self._settings.radon_cc_options or self._analyzer_config.get("tool_options", {}).get("radon_cc", "")
        options = render_command_options(
            self._settings.csv_list(radon_cc_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent)},
        )
        try:
            payload = json.loads(run_command([python, "-m", module, *options], cwd=str(temp_path.parent), timeout=self._settings.analyzer_timeout) or "{}")
        except (AnalyzerError, json.JSONDecodeError) as exc:
            logger.warning("Radon CC unavailable or invalid: %s", exc)
            return []

        threshold = int(self._quality_config.get("max_cyclomatic_complexity"))
        findings: list[Finding] = []
        for _filepath, blocks in payload.items():
            for block in blocks:
                cc = block.get("complexity", 0)
                if cc <= threshold:
                    continue
                severity = "high" if cc >= threshold * 2 else "medium"
                name = block.get("name", "")
                findings.append(
                    build_finding(
                        rule_id="radon-cc",
                        title=f"High cyclomatic complexity in '{name}'",
                        description=f"Function or method '{name}' has cyclomatic complexity {cc}; configured threshold is {threshold}.",
                        severity=severity_from_config(severity),
                        category=str(self._analysis_config.get("quality_category")),
                        line=block.get("lineno"),
                        evidence=f"CC={cc}, rank={block.get('rank')}",
                        tool_source=module,
                        finding_metadata={"complexity": cc, "rank": block.get("rank"), "threshold": threshold},
                    )
                )
        return findings

    def _run_radon_mi(self, python: str, temp_path: Any) -> list[Finding]:
        module = str(self._analyzer_config.get("tool_modules", {}).get("radon"))
        radon_mi_options_str = self._settings.radon_mi_options or self._analyzer_config.get("tool_options", {}).get("radon_mi", "")
        options = render_command_options(
            self._settings.csv_list(radon_mi_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent)},
        )
        try:
            payload = json.loads(run_command([python, "-m", module, *options], cwd=str(temp_path.parent), timeout=self._settings.analyzer_timeout) or "{}")
        except (AnalyzerError, json.JSONDecodeError) as exc:
            logger.warning("Radon MI unavailable or invalid: %s", exc)
            return []

        threshold = float(self._quality_config.get("min_maintainability_index"))
        findings: list[Finding] = []
        for _filepath, data in payload.items():
            mi = data.get("mi", 100.0)
            if mi >= threshold:
                continue
            severity = "high" if mi < threshold / 2 else "medium"
            findings.append(
                build_finding(
                    rule_id="radon-mi",
                    title="Low maintainability index",
                    description=f"File maintainability index is {mi:.1f}; configured threshold is {threshold}.",
                    severity=severity_from_config(severity),
                    category=str(self._analysis_config.get("quality_category")),
                    evidence=f"MI={mi:.1f}, rank={data.get('rank')}",
                    tool_source=module,
                    finding_metadata={"maintainability_index": mi, "rank": data.get("rank"), "threshold": threshold},
                )
            )
        return findings

    def _ast_checks(self, tree: ast.AST) -> list[Finding]:
        findings: list[Finding] = []
        skip_prefixes = tuple(self._quality_config.get("public_name_prefixes_to_skip", []))
        self_names = set(self._quality_config.get("self_parameter_names", []))
        quality_category = str(self._analysis_config.get("quality_category"))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", None)
                start_line = node.lineno
                if end_line and (end_line - start_line) > int(self._quality_config.get("max_function_lines")):
                    length = end_line - start_line
                    findings.append(build_finding(
                        rule_id="ast-long-method",
                        title=f"Long method '{node.name}'",
                        description=f"Method '{node.name}' spans {length} lines.",
                        severity=severity_from_config("medium"),
                        category=quality_category,
                        line=start_line,
                        evidence=f"{length} lines",
                        tool_source=self._ast_tool,
                        finding_metadata={"length": length, "threshold": self._quality_config.get("max_function_lines")},
                    ))

                n_params = len(node.args.args)
                if node.args.args and node.args.args[0].arg in self_names:
                    n_params -= 1
                if n_params > int(self._quality_config.get("max_params")):
                    findings.append(build_finding(
                        rule_id="ast-too-many-params",
                        title=f"Too many parameters in '{node.name}'",
                        description=f"Function '{node.name}' has {n_params} parameters.",
                        severity=severity_from_config("medium"),
                        category=quality_category,
                        line=node.lineno,
                        evidence=f"{n_params} parameters",
                        tool_source=self._ast_tool,
                        finding_metadata={"parameter_count": n_params, "threshold": self._quality_config.get("max_params")},
                    ))

                if not node.name.startswith(skip_prefixes) and ast.get_docstring(node) is None:
                    findings.append(build_finding(
                        rule_id="ast-missing-docstring",
                        title=f"Missing docstring in public function '{node.name}'",
                        description=f"Public function '{node.name}' does not have a docstring.",
                        severity=severity_from_config("low"),
                        category=quality_category,
                        line=node.lineno,
                        evidence=f"def {node.name}(...)",
                        tool_source=self._ast_tool,
                    ))

                max_depth = self._max_nesting_depth(node)
                if max_depth > int(self._quality_config.get("max_nesting")):
                    findings.append(build_finding(
                        rule_id="ast-deep-nesting",
                        title=f"Deep nesting in '{node.name}'",
                        description=f"Function '{node.name}' has nesting depth {max_depth}.",
                        severity=severity_from_config("medium"),
                        category=quality_category,
                        line=node.lineno,
                        evidence=f"Max nesting depth: {max_depth}",
                        tool_source=self._ast_tool,
                        finding_metadata={"nesting_depth": max_depth, "threshold": self._quality_config.get("max_nesting")},
                    ))

            if isinstance(node, ast.ClassDef):
                end_line = getattr(node, "end_lineno", None)
                if end_line and (end_line - node.lineno) > int(self._quality_config.get("max_class_lines")):
                    length = end_line - node.lineno
                    findings.append(build_finding(
                        rule_id="ast-large-class",
                        title=f"Large class '{node.name}'",
                        description=f"Class '{node.name}' spans {length} lines.",
                        severity=severity_from_config("medium"),
                        category=quality_category,
                        line=node.lineno,
                        evidence=f"{length} lines",
                        tool_source=self._ast_tool,
                        finding_metadata={"length": length, "threshold": self._quality_config.get("max_class_lines")},
                    ))
                if not node.name.startswith(skip_prefixes) and ast.get_docstring(node) is None:
                    findings.append(build_finding(
                        rule_id="ast-missing-class-docstring",
                        title=f"Missing docstring in class '{node.name}'",
                        description=f"Class '{node.name}' does not have a docstring.",
                        severity=severity_from_config("low"),
                        category=quality_category,
                        line=node.lineno,
                        evidence=f"class {node.name}",
                        tool_source=self._ast_tool,
                    ))
        return findings

    def _max_nesting_depth(self, root: ast.AST) -> int:
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)

        def depth(node: ast.AST, current: int) -> int:
            if isinstance(node, nesting_nodes):
                current += 1
            return max((depth(child, current) for child in ast.iter_child_nodes(node)), default=current)

        return depth(root, 0)
