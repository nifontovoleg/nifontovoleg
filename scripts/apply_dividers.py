from pathlib import Path

DIVIDER = (
    '\n<div align="center">\n'
    '  <img src="./assets/divider.svg" alt="" width="100%" />\n'
    "</div>\n"
)

for name in ("README.md", "README_RU.md"):
    path = Path(name)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out = []
    for line in lines:
        if line.strip() == "---":
            out.append(DIVIDER)
        else:
            out.append(line)
    path.write_text("".join(out), encoding="utf-8")
    print(f"Updated {name}")
