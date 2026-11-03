#!/usr/bin/env python3
"""Read-only checks for explicit Markdown/TeX paper inputs; not a compiler or audit."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

TOOL_ID = "personal-mathmodel.check-paper.v1"

MARKERS = re.compile(r"\b(?:TODO|TBD|PLACEHOLDER)\b|待填写|待补充|待填|此处填写|示例数据", re.I)
INTERNAL = re.compile(r"(?:\b(?:outputs|reports|validation|code|results)/[^\s{}<>]+|"
                      r"\b(?:ANALYSIS_MODELING_REPORT|RESULTS_REPORT|RUN_RECEIPT|CLAIM_LEDGER)\.(?:md|json))")
COMMAND = re.compile(r"\\(input|include|includegraphics|graphicspath|DeclareGraphicsExtensions|"
                     r"label|(?:eq|page|auto|name)?ref|[cC]ref|(?:cite\w*|nocite)|"
                     r"bibitem|bibliography|addbibresource)\*?(?![A-Za-z@])")


def blank(value: str) -> str:
    return re.sub(r"[^\n]", " ", value)


def tex_visible(text: str) -> str:
    text = re.sub(r"\\begin\{(verbatim\*?|Verbatim|lstlisting|minted)\}.*?\\end\{\1\}",
                  lambda m: blank(m.group()), text, flags=re.S)
    text = re.sub(r"\\verb\*?([^\w\s]).*?\1", lambda m: blank(m.group()), text)
    # An odd run of backslashes escapes %, an even run does not.
    lines = []
    for line in text.splitlines(keepends=True):
        for i, char in enumerate(line):
            if char == "%" and (i - len(line[:i].rstrip("\\"))) % 2 == 0:
                line = line[:i] + blank(line[i:])
                break
        lines.append(line)
    return "".join(lines)


def md_visible(text: str) -> str:
    text = re.sub(r"<!--.*?-->", lambda m: blank(m.group()), text, flags=re.S)
    lines, fence, lists, previous_blank = [], None, [], True
    for line in text.splitlines(keepends=True):
        expanded = line.expandtabs(4)
        indent = len(expanded) - len(expanded.lstrip(" "))
        if fence:
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)", expanded[fence[2]:])
            lines.append(blank(line))
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1] and not marker.group(2).strip():
                fence = None
            previous_blank = not line.strip()
            continue
        base = lists[-1][1] if lists else 0
        entry = re.match(r"^( *)(?:[-+*]|\d+[.)])([ \t]+)(.*)", expanded)
        if entry and indent < base + 4:
            while lists and indent < lists[-1][1]:
                lists.pop()
            base = entry.start(3)
            lists.append((indent, base))
            logical = entry.group(3)
        else:
            if line.strip() and lists:
                if indent < lists[0][1] and previous_blank:
                    lists.clear()
                else:
                    while len(lists) > 1 and indent < lists[-1][1]:
                        lists.pop()
            base = lists[-1][1] if lists else 0
            logical = expanded[base:] if indent >= base else expanded
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)", logical)
        if marker:
            fence = (marker.group(1)[0], len(marker.group(1)), base)
            lines.append(blank(line))
        else:
            lines.append(blank(line) if line.strip() and indent >= base + 4 else line)
        previous_blank = not line.strip()
    text = "".join(lines)
    return re.sub(r"(`+)[^\n]*?\1", lambda m: blank(m.group()), text)


def group(text: str, pos: int, opener: str = "{") -> tuple[str | None, int]:
    """Read one balanced literal group, skipping escaped delimiters."""
    while pos < len(text) and text[pos].isspace():
        pos += 1
    closer = {"{": "}", "[": "]", "(": ")"}[opener]
    if pos >= len(text) or text[pos] != opener:
        return None, pos
    start, depth, pos = pos + 1, 1, pos + 1
    while pos < len(text):
        if text[pos] == "\\":
            pos += 2
            continue
        if text[pos] == opener:
            depth += 1
        elif text[pos] == closer:
            depth -= 1
            if depth == 0:
                return text[start:pos], pos + 1
        pos += 1
    return None, pos


def dynamic(value: str) -> bool:
    return any(c in value for c in "\\#${}")


class Checker:
    def __init__(self, entry: Path, root: Path, allow_markers: bool):
        self.entry, self.root, self.allow_markers = entry, root, allow_markers
        self.issues: list[dict] = []
        self.files: set[Path] = set()
        self.targets: set[Path] = {entry, Path(__file__).resolve()}
        self.active_inputs: list[Path] = []
        self.input_count = 0
        self.labels: dict[str, tuple[Path, int]] = {}
        self.bibs: dict[str, tuple[Path, int]] = {}
        self.refs: list[tuple[str, Path, int, str]] = []
        self.graphics_dirs: list[str] = []
        self.graphics_exts = [".pdf", ".png", ".jpg", ".jpeg", ".eps"]
        self.unknown_labels = False
        self.unknown_bibs = False

    def add(self, level: str, code: str, path: Path, line: int, message: str):
        item = dict(level=level, code=code, file=str(path), line=line, message=message)
        if item not in self.issues:
            self.issues.append(item)

    def inside(self, path: Path) -> bool:
        return path.is_relative_to(self.root)

    def read(self, path: Path) -> str:
        self.targets.add(path)
        if not self.inside(path):
            raise ValueError("text dependency leaves --root")
        if path.stat().st_size > 2_000_000:
            raise ValueError("text dependency exceeds 2 MB; inspect it separately")
        return path.read_text(encoding="utf-8-sig")

    def prose(self, visible: str, path: Path):
        # Source sections end at the next same/higher heading, not end-of-file.
        lines, excluded_level = [], None
        levels = {"section": 1, "subsection": 2, "subsubsection": 3,
                  "paragraph": 4, "subparagraph": 5}
        for line in visible.splitlines(keepends=True):
            md = re.match(r"^ {0,3}(#{1,6})\s+(.+)", line)
            tex = re.match(r"^\s*\\(section|subsection|subsubsection|paragraph|subparagraph)\*?\s*\{", line)
            level, title = None, ""
            if md:
                level, title = len(md.group(1)), md.group(2)
            elif tex:
                level = levels[tex.group(1)]
                title, _ = group(line, tex.end() - 1)
                title = title or ""
            if level is not None:
                if excluded_level is not None and level <= excluded_level:
                    excluded_level = None
                if re.search(r"源码|程序代码|代码清单", title):
                    excluded_level = level
            lines.append(blank(line) if excluded_level is not None else line)
        body = "".join(lines)
        if not self.allow_markers:
            for match in MARKERS.finditer(body):
                self.add("error", "placeholder", path, body.count("\n", 0, match.start()) + 1,
                         f"Unfilled marker: {match.group()}")
        for match in INTERNAL.finditer(body):
            self.add("warning", "internal-path", path, body.count("\n", 0, match.start()) + 1,
                     f"Possible internal workflow reference in prose: {match.group()}")

    def local_target(self, value: str, path: Path, line: int, kind: str,
                     extensions: list[str] | None = None) -> Path | None:
        value = value.strip()
        if kind == "Markdown link":
            if urlsplit(value).scheme or value.startswith("//"):
                self.add("review", "remote-link", path, line, f"Remote target not checked offline: {value}")
                return None
            value = value.split("#", 1)[0].split("?", 1)[0]
            if not value:
                return None  # Anchor content remains outside this check.
        if dynamic(value):
            self.add("review", "dynamic-path", path, line, f"Cannot resolve {kind}: {value}")
            return None
        if urlsplit(value).scheme or value.startswith("//"):
            self.add("review", "remote-link", path, line, f"Remote target not checked offline: {value}")
            return None
        value = unquote(value) if kind == "Markdown link" else value
        if not value:
            return None  # Same-page Markdown anchors are outside this check.
        raw = Path(value)
        bases = [self.entry.parent] if kind != "Markdown link" else [path.parent]
        if kind == "image":
            bases += [self.entry.parent / d for d in self.graphics_dirs]
        candidates = [raw] if raw.is_absolute() else [b / raw for b in bases]
        expanded = []
        for candidate in candidates:
            expanded += [candidate] if candidate.suffix or not extensions else [Path(str(candidate) + ext) for ext in extensions]
        self.targets.update(p.resolve() for p in expanded)
        safe = [p.resolve() for p in expanded if self.inside(p.resolve())]
        if not safe:
            self.add("review", "outside-root", path, line, f"Target outside --root was not opened: {value}")
            return None
        for target in safe:
            if target.is_file():
                return target
        self.add("error", "missing-target", path, line, f"Missing {kind}: {value}")
        return None

    def markdown(self, path: Path):
        text = md_visible(self.read(path))
        self.files.add(path)
        self.prose(text, path)
        normalize = lambda key: re.sub(r"\s+", " ", key).strip().casefold()
        definitions = {normalize(m.group(1)): (m.group(2), m.start()) for m in
                       re.finditer(r"(?m)^\s*\[([^]]+)\]:\s*(<[^>]+>|\S+)", text)}
        # Balanced destinations preserve legitimate names such as fig(a).png.
        for match in re.finditer(r"!?\[[^]\n]*\]\(", text):
            value, _ = group(text, match.end() - 1, "(")
            line = text.count("\n", 0, match.start()) + 1
            token = re.match(r"\s*(<[^>]*>|(?:\\.|[^\s])+)", value or "")
            if value is None or token is None:
                self.add("review", "unsupported-markdown-link", path, line, "Cannot resolve Markdown destination")
                continue
            dest = token.group(1).removeprefix("<").removesuffix(">")
            dest = re.sub(r"\\([\\()\[\] ])", r"\1", dest)
            self.local_target(dest, path, line, "Markdown link")
        for match in re.finditer(r"!?\[([^]\n]+)\]\[([^]\n]*)\]", text):
            key = normalize(match.group(2) or match.group(1))
            line = text.count("\n", 0, match.start()) + 1
            if key not in definitions:
                self.add("error", "missing-link-definition", path, line, f"Missing link definition: {key}")
            else:
                value, _ = definitions[key]
                self.local_target(value.strip("<>"), path, line, "Markdown link")
        for match in re.finditer(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", text, re.I):
            self.local_target(match.group(1), path, text.count("\n", 0, match.start()) + 1, "Markdown link")

    def declare(self, name: str, table: dict, path: Path, line: int):
        if name in table:
            first, first_line = table[name]
            self.add("error", "duplicate-label" if table is self.labels else "duplicate-citation-key",
                     path, line, f"Duplicate {name}; first at {first}:{first_line}")
        else:
            table[name] = (path, line)

    def tex(self, path: Path, source: Path | None = None, source_line: int = 1):
        if path in self.active_inputs:
            self.add("error", "cyclic-input", source or path, source_line,
                     "Cyclic literal TeX input: " + " -> ".join(p.name for p in self.active_inputs + [path]))
            return
        if self.input_count >= 128:
            self.add("review", "file-limit", source or path, source_line, "128-input expansion limit reached")
            self.unknown_labels = self.unknown_bibs = True
            return
        self.input_count += 1
        self.active_inputs.append(path)
        try:
            self._tex(path)
        finally:
            self.active_inputs.pop()

    def _tex(self, path: Path):
        try:
            text = tex_visible(self.read(path))
        except (OSError, UnicodeError, ValueError) as exc:
            if path == self.entry:
                raise
            self.add("review", "unreadable-dependency", path, 1, str(exc))
            self.unknown_labels = self.unknown_bibs = True
            return
        self.files.add(path)
        # Never execute literal input commands embedded inside a macro definition.
        defs = r"\\(newcommand|renewcommand|providecommand|DeclareRobustCommand|def|gdef|edef|xdef)\*?(?![A-Za-z@])"
        for definition in list(re.finditer(defs, text)):
            pos = definition.end()
            while pos < len(text) and text[pos].isspace(): pos += 1
            if pos < len(text) and text[pos] == "{":
                _, pos = group(text, pos)
            else:
                name = re.match(r"\\(?:[A-Za-z@]+|.)", text[pos:])
                if not name: continue
                pos += name.end()
            if definition.group(1) in {"def", "gdef", "edef", "xdef"}:
                start = text.find("{", pos)
                if start == -1: continue
                pos = start
            while True:
                opt, end = group(text, pos, "[")
                if opt is None: break
                pos = end
            body, end = group(text, pos)
            if body is not None:
                if not self.allow_markers and MARKERS.search(body):
                    self.add("review", "macro-placeholder", path, text.count("\n", 0, definition.start()) + 1,
                             "Unexpanded macro contains an unfilled marker; confirm whether it enters the paper")
                if COMMAND.search(body):
                    self.add("review", "macro-structure", path, text.count("\n", 0, definition.start()) + 1,
                             "A macro contains structural commands; its expansion was not interpreted")
                    self.unknown_labels |= bool(re.search(r"\\label\b", body))
                    self.unknown_bibs |= bool(re.search(r"\\(?:bibitem|bibliography|addbibresource)\b", body))
                    if re.search(r"\\(?:input|include)\b", body):
                        self.unknown_labels = self.unknown_bibs = True
                text = text[:definition.start()] + blank(text[definition.start():end]) + text[end:]
        self.prose(text, path)
        for match in COMMAND.finditer(text):
            command, pos = match.group(1), match.end()
            while True:
                opt, end = group(text, pos, "[")
                if opt is None:
                    break
                pos = end
            value, _ = group(text, pos)
            line = text.count("\n", 0, match.start()) + 1
            if value is None:
                self.add("review", "nonliteral-command", path, line, f"Unsupported/unbalanced \\{command} argument")
                continue
            if command == "graphicspath":
                dirs = re.findall(r"\{([^{}]*)\}", value)
                if not dirs or any(dynamic(d) for d in dirs):
                    self.add("review", "dynamic-graphics-path", path, line, "Cannot resolve graphicspath")
                else:
                    self.graphics_dirs = dirs
            elif command == "DeclareGraphicsExtensions":
                self.graphics_exts = [v.strip() for v in value.split(",") if v.strip().startswith(".")]
            elif command in {"input", "include", "includegraphics"}:
                image = command == "includegraphics"
                target = self.local_target(value, path, line, "image" if image else "TeX input",
                                           self.graphics_exts if image else [".tex"])
                if target and not image:
                    if target.suffix.lower() in {".tex", ".sty", ".cls"}:
                        self.tex(target, path, line)
                    else:
                        self.add("review", "unsupported-input", path, line, "Only explicit .tex/.sty/.cls text dependencies are read")
                elif not image:
                    self.unknown_labels = self.unknown_bibs = True
            elif command == "label" or command == "bibitem":
                if dynamic(value):
                    if command == "label": self.unknown_labels = True
                    else: self.unknown_bibs = True
                    self.add("review", "dynamic-key", path, line, f"Cannot resolve \\{command} key")
                else:
                    self.declare(value, self.labels if command == "label" else self.bibs, path, line)
            elif command in {"bibliography", "addbibresource"}:
                for bib in value.split(","):
                    target = self.local_target(bib, path, line, "bibliography", [".bib"])
                    if target:
                        try:
                            bibtext = self.read(target)
                            self.files.add(target)
                            for item in re.finditer(r"(?im)^\s*@(?!comment\b|string\b|preamble\b)\w+\s*[\{(]\s*([^,\s]+)\s*,", bibtext):
                                self.declare(item.group(1), self.bibs, target, bibtext.count("\n", 0, item.start()) + 1)
                        except (OSError, UnicodeError, ValueError) as exc:
                            self.add("review", "unreadable-bibliography", path, line, str(exc))
                            self.unknown_bibs = True
                    else:
                        self.unknown_bibs = True
            elif command == "citetext":
                continue  # natbib's citetext contains prose, not citation keys.
            else:
                citation = command.startswith("cite") or command == "nocite"
                if dynamic(value):
                    self.add("review", "dynamic-key", path, line, f"Cannot resolve \\{command} key")
                else:
                    for key in value.split(","):
                        if key.strip() and key.strip() != "*":
                            self.refs.append((key.strip(), path, line, "citation" if citation else "reference"))

    def result(self) -> dict:
        if self.entry.suffix.lower() == ".md":
            self.markdown(self.entry)
        elif self.entry.suffix.lower() == ".tex":
            self.tex(self.entry)
            for key, path, line, kind in self.refs:
                table, unknown = (self.bibs, self.unknown_bibs) if kind == "citation" else (self.labels, self.unknown_labels)
                if key not in table:
                    self.add("review" if unknown else "error", "unresolved-" + kind, path, line,
                             f"No literal declaration found for {kind}: {key}")
        else:
            raise ValueError("Entry must end in .md or .tex")
        self.issues.sort(key=lambda x: (x["file"], x["line"], x["code"]))
        counts = {level: sum(x["level"] == level for x in self.issues) for level in ["error", "review", "warning"]}
        code = 1 if counts["error"] else 3 if counts["review"] else 0
        return dict(tool_id=TOOL_ID, entry=str(self.entry), root=str(self.root), template_mode=self.allow_markers,
                    status="errors_found" if code == 1 else "needs_review" if code == 3 else "no_detected_errors",
                    exit_code=code, counts=counts, files_read=[str(p) for p in sorted(self.files)],
                    dependency_targets=[str(p) for p in sorted(self.targets)], issues=self.issues,
                    limits=["Static literal checks only; macros/classes/packages and all TeX syntax are not interpreted.",
                            "No numerical, scientific, citation-authenticity, complete language, compilation or visual verification.",
                            "Remote URLs and unsupported dynamic targets are not fetched; Markdown anchors are not validated."])


def write_report(requested: Path, report: dict, checker: Checker, overwrite: bool):
    """Refuse source/alias collisions and unmarked existing files before writing."""
    requested = requested.expanduser().absolute()
    target = requested.resolve()
    if target.suffix.lower() != ".json" or requested.is_symlink():
        raise ValueError("Report must be a distinct .json file, not a symbolic link")
    for dependency in checker.targets | checker.files:
        if target == dependency or (target.exists() and dependency.exists() and os.path.samefile(target, dependency)):
            raise ValueError("Report collides with an input/dependency target")
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        with target.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        return
    if not target.exists():
        with target.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        return
    previous = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(previous, dict) or previous.get("tool_id") != TOOL_ID:
        raise ValueError("Only an identified report from this tool may be overwritten")
    # Atomic replacement leaves other hard-link names unchanged.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".paper-check-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> int:
    if sys.version_info < (3, 9):
        print("This checker requires Python 3.9 or newer; use the existing project interpreter.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path, help="Explicit .md or .tex entry")
    parser.add_argument("--root", type=Path, help="Allowed dependency root (default: entry's parent)")
    parser.add_argument("--json", type=Path, help="Only this explicit JSON report is written")
    parser.add_argument("--overwrite-report", action="store_true", help="Replace only an identified previous report; never an input")
    parser.add_argument("--allow-template-markers", action="store_true", help="Allow unfilled prose markers in a template")
    args = parser.parse_args()
    entry = args.entry.resolve()
    root = (args.root or entry.parent).resolve()
    try:
        if not entry.is_relative_to(root) or not entry.is_file():
            raise ValueError("Entry must be an existing file inside --root")
        checker = Checker(entry, root, args.allow_template_markers)
        report = checker.result()
        if args.json:
            write_report(args.json, report, checker, args.overwrite_report)
        print(f"{report['status']}: {report['counts']}")
        for issue in report["issues"]:
            print(f"{issue['level'].upper()} {issue['file']}:{issue['line']} [{issue['code']}] {issue['message']}")
        print("Static checks only; this is not paper acceptance.")
        return report["exit_code"]
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"check could not complete: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
