import html
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INTRO = "README.md"
PARTS = ["01-firmware.md", "02-tests-and-tools.md"]
OUT = HERE / "code-explained.html"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
LINE_LINK_RE = re.compile(r"\[L(\d+)(?:[–-](\d+))?\]\(([^)#]+)#L\d+\)")


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def inline(text: str, md_dir: pathlib.Path = HERE) -> str:
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = html.escape(text, quote=False)

    def link(m):
        label, url = m.group(1), m.group(2)
        if url.endswith(".md"):
            return f'<a href="#{pathlib.Path(url).stem}">{label}</a>'
        if url.startswith("http"):
            return f'<a href="{url}">{label}</a>'
        if "#L" in url:
            path, line = url.split("#L")
            target = (md_dir / path).resolve().as_posix()
            return f'<a class="lref" href="vscode://file/{target}:{line}" title="Open in VS Code">{label}</a>'
        return f"<code>{label}</code>"

    text = LINK_RE.sub(link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<i>\1</i>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(codes[int(m.group(1))], quote=False)}</code>", text)


def cells(row: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", row.strip())
    return [p.strip().replace("\\|", "|") for p in parts[1:-1]]


def source_block(cell: str, md_dir: pathlib.Path) -> str:
    m = LINE_LINK_RE.search(cell)
    if not m:
        return ""
    start, end = int(m.group(1)), int(m.group(2) or m.group(1))
    lines = (md_dir / m.group(3)).resolve().read_text(encoding="utf-8").splitlines()
    body = "".join(
        f'<span class="l"><span class="ln">{n}</span>{html.escape(lines[n - 1]) or " "}</span>'
        for n in range(start, end + 1)
    )
    return f'<pre class="src">{body}</pre>'


def render_table(rows: list[str], md_dir: pathlib.Path) -> str:
    head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
    annotated = head[0] == "Lines"
    if annotated:
        drop = 1 if len(head) > 1 and head[1] == "Code" else None
        rest = [i for i in range(1, len(head)) if i != drop]
        head = [head[0], "Code", *(head[i] for i in rest)]
        body = [[r[0], source_block(r[0], md_dir), *(r[i] for i in rest)] for r in body]
    out = [f'<div class="table-wrap"><table class="{"annot" if annotated else "plain"}"><thead><tr>']
    out += [f"<th>{inline(h, md_dir)}</th>" for h in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for i, c in enumerate(r):
            cls = ["lines", "code"][i] if annotated and i < 2 else ""
            content = c if annotated and i == 1 else inline(c, md_dir)
            out.append(f'<td class="{cls}">{content}</td>' if cls else f"<td>{content}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_md(path: pathlib.Path, part_id: str, toc: list, skip_title: bool = False) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            out.append(f'<pre class="diagram">{html.escape(chr(10).join(lines[i + 1:j]))}</pre>')
            i = j + 1
            continue
        if line.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            out.append(render_table(lines[i:j], path.parent))
            i = j
            continue
        m = re.match(r"(#{1,3}) (.*)", line)
        if m:
            level, text = len(m.group(1)), inline(m.group(2))
            if level == 1:
                if not skip_title:
                    out.append(f'<h2 class="part" id="{part_id}">{text}</h2>')
                    toc.append((1, part_id, text))
            elif level == 2:
                sid = f"{part_id}-{slug(text)}"
                out.append(f'<h3 id="{sid}">{text}</h3>')
                toc.append((2, sid, text))
            else:
                out.append(f"<h4>{text}</h4>")
            i += 1
            continue
        if line.startswith("> "):
            out.append(f'<p class="note">{inline(line[2:], path.parent)}</p>')
        elif line.startswith("- "):
            j = i
            items = []
            while j < len(lines) and lines[j].startswith("- "):
                items.append(f"<li>{inline(lines[j][2:])}</li>")
                j += 1
            out.append(f"<ul>{''.join(items)}</ul>")
            i = j
            continue
        elif line.strip() and line.strip() != "---":
            j = i
            para = []
            while j < len(lines) and lines[j].strip() and not re.match(r"(#|\||```|> |- |---)", lines[j]):
                para.append(lines[j].strip())
                j += 1
            out.append(f"<p>{inline(' '.join(para), path.parent)}</p>")
            i = j
            continue
        i += 1
    return "\n".join(out)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Code Explained</title>
<style>
:root {
  --bg: #f6f5f1; --surface: #fdfcfa; --border: #dedad0; --text: #14202b; --muted: #5a6573;
  --accent: #c2410c; --link: #1d5fd0; --code-bg: #f1efe8; --code-text: #1f2a36; --ln: #9aa3ad;
  --head: #ece9e1; --hit: #fff1c2;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #11181f; --surface: #172029; --border: #2a3542; --text: #e8edf2; --muted: #9aa7b4;
    --accent: #ff9a5c; --link: #7fb2ff; --code-bg: #0d1319; --code-text: #d8e0e8; --ln: #56636f;
    --head: #1d2833; --hit: #4a3d12;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
a { color: var(--link); }
code, pre { font-family: "Cascadia Code", Consolas, "JetBrains Mono", monospace; }
code { font-size: .88em; background: var(--code-bg); padding: 1px 5px; border-radius: 4px; }
.layout { display: grid; grid-template-columns: 270px minmax(0, 1fr); min-height: 100vh; }
nav { position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 24px 18px;
  border-right: 1px solid var(--border); background: var(--surface); }
nav .title { font-weight: 700; font-size: 1.05rem; margin: 0 0 4px; }
nav .sub { color: var(--muted); font-size: .82rem; margin: 0 0 16px; }
nav input { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); font: inherit; margin-bottom: 16px; }
nav ol { list-style: none; margin: 0; padding: 0; }
nav li a { display: block; padding: 3px 8px; border-radius: 6px; text-decoration: none; color: var(--text); font-size: .88rem; }
nav li a:hover { background: var(--head); }
nav li.l1 { margin-top: 12px; }
nav li.l1 a { font-weight: 650; }
nav li.l2 a { padding-left: 18px; color: var(--muted); }
main { padding: 32px 40px 80px; max-width: 1500px; }
h1 { font-size: 1.9rem; margin: 0 0 8px; }
h2.part { font-size: 1.55rem; margin: 56px 0 12px; padding-top: 12px; border-top: 3px solid var(--accent); }
h3 { font-size: 1.2rem; margin: 36px 0 10px; }
h4 { font-size: 1rem; margin: 24px 0 8px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
p.note { color: var(--muted); font-style: italic; }
pre.diagram { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; overflow-x: auto; font-size: .85rem; line-height: 1.35; }
.table-wrap { overflow-x: auto; margin: 10px 0 18px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
table { width: 100%; border-collapse: collapse; }
table.annot { table-layout: fixed; min-width: 900px; }
th { background: var(--head); text-align: left; font-size: .8rem; text-transform: uppercase;
  letter-spacing: .04em; color: var(--muted); padding: 8px 12px; }
td { padding: 10px 12px; border-top: 1px solid var(--border); vertical-align: top; }
table.annot th:nth-child(1) { width: 92px; }
table.annot th:nth-child(2) { width: 48%; }
table.annot:has(th:nth-child(4)) th:nth-child(2) { width: 42%; }
table.annot:has(th:nth-child(4)) th:nth-child(3) { width: 150px; }
td.lines { white-space: nowrap; }
.lref { display: inline-block; font: 600 .8rem/1.4 Consolas, monospace; color: var(--accent);
  background: var(--code-bg); padding: 2px 7px; border-radius: 6px; text-decoration: none; }
a.lref:hover { outline: 1px solid var(--accent); }
td.code { padding: 6px; }
pre.src { margin: 0; background: var(--code-bg); color: var(--code-text); border-radius: 6px; padding: 8px 10px;
  font-size: .8rem; line-height: 1.45; overflow-y: auto; max-height: 420px; }
pre.src .l { display: block; white-space: pre-wrap; overflow-wrap: anywhere; padding-left: 3.5em; text-indent: -3.5em; }
pre.src .ln { display: inline-block; width: 2.6em; margin-right: .9em; text-align: right; text-indent: 0; color: var(--ln); user-select: none; }
tr.hit td { background: var(--hit); }
tr.hide, .table-wrap.hide { display: none; }
footer { margin-top: 64px; color: var(--muted); font-size: .82rem; }
@media (max-width: 900px) {
  .layout { display: block; }
  nav { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--border); }
  nav ol { display: none; }
  main { padding: 20px 16px 60px; }
}
</style>
</head>
<body>
<div class="layout">
<nav>
  <p class="title">Code Explained</p>
  <p class="sub">Environmental Monitoring Station</p>
  <input id="filter" type="search" placeholder="Filter rows (e.g. watchdog, seq, LWT)" aria-label="Filter rows">
  <ol>__TOC__</ol>
</nav>
<main>
<h1>Code Explained — Environmental Monitoring Station</h1>
__BODY__
<footer>Generated from <code>docs/code-explained/*.md</code>. After editing those files, run
<code>python docs/code-explained/build_html.py</code> to rebuild this page.</footer>
</main>
</div>
<script>
const input = document.getElementById("filter");
input.addEventListener("input", () => {
  const q = input.value.trim().toLowerCase();
  for (const tr of document.querySelectorAll("tbody tr")) {
    const match = q && tr.textContent.toLowerCase().includes(q);
    tr.classList.toggle("hit", Boolean(match));
    tr.classList.toggle("hide", Boolean(q) && !match);
  }
  for (const wrap of document.querySelectorAll(".table-wrap")) {
    wrap.classList.toggle("hide", Boolean(q) && !wrap.querySelector("tbody tr:not(.hide)"));
  }
});
</script>
</body>
</html>
"""


def main():
    toc = []
    body = [render_md(HERE / INTRO, "intro", toc, skip_title=True)]
    for name in PARTS:
        body.append(render_md(HERE / name, pathlib.Path(name).stem, toc))
    nav = "".join(f'<li class="l{lvl}"><a href="#{sid}">{text}</a></li>' for lvl, sid, text in toc)
    OUT.write_text(PAGE.replace("__TOC__", nav).replace("__BODY__", "\n".join(body)), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
