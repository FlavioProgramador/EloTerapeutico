#!/usr/bin/env python3
"""Gera um resumo de cobertura por módulo a partir do coverage.xml."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree  # nosec B405


def module_name(filename: str) -> str:
    parts = Path(filename).parts
    if "apps" in parts:
        index = parts.index("apps")
        if len(parts) > index + 1:
            return parts[index + 1]
    if parts and parts[0] == "core":
        return "core"
    return "shared"


def load_report(path: Path) -> dict[str, dict[str, float | int]]:
    root = ElementTree.parse(path).getroot()  # nosec B314
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"lines_valid": 0, "lines_covered": 0, "branches_valid": 0, "branches_covered": 0}
    )

    for class_node in root.findall(".//class"):
        filename = class_node.attrib.get("filename", "")
        module = module_name(filename)
        lines = class_node.findall("./lines/line")
        totals[module]["lines_valid"] += len(lines)
        totals[module]["lines_covered"] += sum(int(line.attrib.get("hits", "0")) > 0 for line in lines)

        for line in lines:
            if line.attrib.get("branch") != "true":
                continue
            condition = line.attrib.get("condition-coverage", "0% (0/0)")
            fraction = condition.split("(")[-1].rstrip(")")
            try:
                covered, valid = (int(value) for value in fraction.split("/"))
            except (TypeError, ValueError):
                continue
            totals[module]["branches_valid"] += valid
            totals[module]["branches_covered"] += covered

    report: dict[str, dict[str, float | int]] = {}
    for module, values in sorted(totals.items()):
        line_total = values["lines_valid"]
        branch_total = values["branches_valid"]
        report[module] = {
            **values,
            "line_rate": round(values["lines_covered"] / line_total * 100, 2) if line_total else 100.0,
            "branch_rate": round(values["branches_covered"] / branch_total * 100, 2) if branch_total else 100.0,
        }
    return report


def markdown(report: dict[str, dict[str, float | int]]) -> str:
    rows = [
        "# Cobertura por módulo",
        "",
        "| Módulo | Linhas | Branches | Linhas cobertas |",
        "|---|---:|---:|---:|",
    ]
    for module, values in report.items():
        rows.append(
            f"| {module} | {values['line_rate']:.2f}% | {values['branch_rate']:.2f}% | "
            f"{values['lines_covered']}/{values['lines_valid']} |"
        )
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", default="coverage.xml")
    parser.add_argument("--markdown", default="coverage-by-module.md")
    parser.add_argument("--json", default="coverage-by-module.json")
    args = parser.parse_args()

    xml_path = Path(args.xml)
    if not xml_path.exists():
        raise SystemExit(f"Relatório não encontrado: {xml_path}")

    report = load_report(xml_path)
    markdown_text = markdown(report)
    Path(args.markdown).write_text(markdown_text, encoding="utf-8")
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(markdown_text)

    print(markdown_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
