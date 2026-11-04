# Excalidraw README diagrams

Companion code for "Hand-Drawn README Diagrams with the Excalidraw CLI". It holds the
`readme-diagram` Claude Code skill from the post, the script it runs, and the spec behind the
post's figure.

Needs Python 3.10 or later for the script, and the
[Excalidraw CLI](https://github.com/excalidraw/cli) (Node.js 22 or later, plus Chrome, Chromium,
Edge or Firefox) for rendering.

## Install the skill

```bash
npm i -g @excalidraw/cli
cp -R skills/readme-diagram ~/.claude/skills/
```

Then ask Claude Code in any project for a README diagram: "add a diagram to the README that shows
how this project works, from the architecture doc". The skill reads the project's text diagram,
writes a spec to `docs/diagrams/overview.json`, builds and renders it, looks at both PNGs and
embeds them in the README with a `<picture>` element.

## Render the example

```bash
python3 skills/readme-diagram/scripts/build_scene.py \
  example/blog.json \
  example/blog.excalidraw

for t in light dark; do
  excalidraw render example/blog.excalidraw \
    --theme $t \
    --scale 2 \
    --out example/blog-$t.png
done
```

The build prints the PNG size to expect and nothing else: the example has no layout warnings.
Move a box in `blog.json` (say `readers` to `"col": 1.6`) and build again to see what a warning
looks like.

| File | Shows |
|---|---|
| `skills/readme-diagram/SKILL.md` | The steps the agent follows, from picking the boxes to the README snippet |
| `skills/readme-diagram/scripts/build_scene.py` | Spec to `.excalidraw`, with layout warnings and `--check` |
| `example/blog.json` | The spec behind the post's figure |
| `example/blog.excalidraw` | The scene it builds, which also opens on excalidraw.com |
| `tests/test_build_scene.py` | Determinism, the warnings, ellipse clipping, `--check` |

```bash
python3 -m unittest discover -s tests
```

## Why a spec instead of the scene

An `.excalidraw` file stores about 30 fields per element, and every arrow and label points at the
box it belongs to. The example's 932-byte spec builds a 21 KB scene of 22 elements. The spec is
what an agent, or a person, edits; the scene is generated. The build is deterministic, so
`--check` can tell a scene edited by hand on excalidraw.com from one the spec built, and the
skill asks before overwriting those edits.

The warnings use estimated text widths, so a clean build doesn't prove a clean picture. That is
why the skill renders and looks at both PNGs before it finishes.
