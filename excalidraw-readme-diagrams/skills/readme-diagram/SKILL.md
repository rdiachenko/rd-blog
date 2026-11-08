---
name: readme-diagram
description: Turn a project's text diagram (usually the context diagram in docs/architecture.md) into a hand-drawn Excalidraw picture for the README, rendered locally to light and dark PNGs with the official Excalidraw CLI and embedded with a <picture> tag so GitHub shows the one matching the reader's theme. Use when the user asks for a README diagram, an overview or architecture picture for users, a PNG of the architecture, an Excalidraw version of a diagram, or to refresh the README diagram after the architecture changed. Also use it for a hand-drawn figure in a blog post, TIL or docs page that explains a flow, a decision or how parts fit together. Not for diagrams inside architecture or design docs, which stay as text for agents to read and edit.
---

# README diagram

A README is read by people who are deciding whether to use the project, so its diagram should be
a picture, not box-drawing characters. The text diagrams in `docs/architecture.md` stay the source
of truth: agents read and edit them, and this skill derives the picture from them. So the picture
uses the same names as the doc, only simplified for a first-time reader.

The same pipeline makes figures for a blog post, TIL or docs page. A figure differs in 2 ways,
covered where they matter below: it shows the page's argument rather than the project, and the
page shrinks it into a text column, so text size and height need checking.

The pipeline is deterministic except for one step, the layout, which you check by looking:

```
text diagram ──► docs/diagrams/<name>.json (spec you write)
             ──► build_scene.py ──► <name>.excalidraw + layout warnings
             ──► excalidraw render ──► <name>-light.png, <name>-dark.png ──► you look, adjust
             ──► README <picture>
```

## 1. Check the tools

Run `excalidraw --version`. If it's missing: `npm i -g @excalidraw/cli` (needs Node 22+, and
Chrome, Chromium, Edge or Firefox installed). Rendering local files needs no account or API key,
so never run `excalidraw login` for this.

## 2. Decide what the picture shows

Read the source diagram (the user's choice, else the context diagram in `docs/architecture.md`,
else the README's own description) and the README's opening paragraphs. Then cut it down for a
reader who has never seen the project:

- 4 to 8 boxes. Keep the reader, the project, what it talks to, and what starts it when the
  README tells the reader to set that up (a schedule, a CI job). Internals (skills, modules,
  files) go into one box's note line, or go away. When the project has 2 parts the reader deals
  with (a CLI and its server), both can be `system` boxes.
- Use the doc's names, so a reader who later opens the architecture doc recognises every box.
- Every arrow says what moves, in 2 to 5 words: `reads, edits, commits`, not `uses`. When the doc
  says more, keep what the reader acts on and drop the rest.
- Name the reader `You` when the README speaks to its user, even if the doc says "Owner".
- Add a boundary (a dashed box) only when where something runs matters to the reader, such as
  "Cloudflare" around the parts they deploy. Around a single box with arrows on every side, it
  only adds lines for labels to collide with.
- Dash an edge only when the difference matters to the reader (optional, async, some setups
  only), and then add a note that says what dashed means.

Diagram for the reader, not for completeness: a missing detail costs nothing, a crowded picture
costs the whole diagram.

For a figure in a post, draw the flow the text explains, not the project's architecture:
- Each box is a step the reader follows in the text, named in their words. Explain jargon in the
  prose first and keep it out of box titles.
- When the flow branches, make the branch point a `decision` node (a diamond) whose label is the
  question ("Is v0 a release tag?"), and label its out-edges with the answers ("yes: 0.44 s",
  "no (main): 22 s or more"). Conditions written on plain arrows ("release tag", "other refs")
  read as statements, and readers miss that the flow branches.
- Leave out a final box that every branch reaches when the edge labels already say the outcome.
- Keep side notes out of the picture: a floating note reads as disconnected. Put its point in the
  paragraph next to the figure.

## 3. Write the spec

Save it as `docs/diagrams/<name>.json` (`overview` unless the user names it). Committed next to
the outputs, it lets the next run change one line instead of redrawing.

```json
{
  "font": "hand",
  "grid": {"col": 320, "row": 220},
  "nodes": [
    {"id": "user", "label": "You", "kind": "person", "col": 1, "row": 0},
    {"id": "app", "label": "linkcheck", "note": "Rust CLI", "kind": "system", "col": 1, "row": 1},
    {"id": "web", "label": "Linked websites", "kind": "external", "col": 2.2, "row": 1}
  ],
  "edges": [
    {"from": "user", "to": "app", "label": "runs, reads the report"},
    {"from": "app", "to": "web", "label": "HTTPS GET", "dashed": true}
  ],
  "notes": [{"id": "key", "text": "dashed: only with --online", "col": 1.6, "row": 1.5}]
}
```

Every field:
- Top level: `font` is `hand` (Excalifont, the Excalidraw look; default), `normal` (Nunito) or
  `code`. `grid` sets the unit in pixels (default col 300, row 170). `fontSize` (box titles,
  default 20) and `edgeFontSize` (arrow labels, boundary titles and notes, default 16). `column`
  is the width in pixels of the text column a page shrinks a figure to (about 700 for a typical
  blog); set it for figures only, see step 4.
- Nodes: `col`, `row` place the box centre in grid units; fractions and negatives are fine
  (`"row": -0.2` lifts one box to make room for the labels below it). `kind` is `person`
  (ellipse), `system` (the project, bold outline), `external`, `store` (repo, database, files),
  `trigger` (scheduler, webhook), `decision` (a flowchart question, drawn as a diamond sized to
  fit its text; keep it to a short question, split with `\n`) or `plain`. Colours come from
  Excalidraw's palette, which its dark theme inverts cleanly, so don't set them by hand. `note` is a smaller grey line under the
  title; `\n` splits it, which keeps a wide note from widening its column. `w`, `h` override the
  size, which otherwise fits the text.
- Boundaries: `label`, `nodes` (ids it surrounds), `padding` (default 40px).
- Edges: `from`, `to`, `label`. `both: true` puts arrowheads on both ends. `dashed: true`.
  `offset: <px>` shifts a straight edge sideways: positive moves it to the right of its direction
  of travel (a downward edge moves to the screen's left), so a pair of opposite edges with the
  same positive offset separate. `via: [[col, row], ...]` routes it through points (curved).
  `wrap: <chars>` sets where the label wraps (default 26); a `\n` in the label breaks the line
  where you want it, and `wrap` still applies to each part. `color` overrides the stroke.
- Notes: free text with `id`, `text`, `col`, `row`, optional `fontSize`.

## 4. Build, render, look

Build:

```sh
python3 ~/.claude/skills/readme-diagram/scripts/build_scene.py docs/diagrams/<name>.json docs/diagrams/<name>.excalidraw
```

The build prints the PNG size to expect and `layout:` warnings for what it can measure: labels
overlapping labels, boxes or boundary lines; a label that leaves too little of its arrow; an
arrow crossing a box or a boundary title; an image over 1800px wide. Fix every warning in the
spec and build again before rendering: building takes no time, rendering and looking do. The
warnings use estimated text widths, so a clean build is necessary, not sufficient. Keep build and
render as separate commands, so a warning can't scroll past on its way to a render.

With `column` set, the build skips the README width limit and reports how the figure reads once the
page shrinks it, for example `in a 700px column: text about 16-21px, about 700x552px`. It warns when
the smallest text drops under 15px, and when the figure shows taller than wide, which fills the
screen on a large monitor. The defaults (20 and 16) end up around 12px in a 700px column; 28 and 24
on a landscape layout about 950 units wide read comfortably.

Render, only after a clean build:

```sh
for t in light dark; do
  excalidraw render docs/diagrams/<name>.excalidraw --theme $t --scale 2 --out docs/diagrams/<name>-$t.png
done
```

`--scale 2` suits a README: GitHub shows the image at half its pixel width, so it stays sharp on
high-density screens. `render` caps output at 2048px wide by default (`--max-width`), which the
1800px limit keeps you under. For a figure, render for the widest the image is shown at, doubled,
and raise the height cap too, since `render` also caps output at 2048px high (`--max-height`) and
quietly lowers the scale of a tall figure to fit:

```sh
excalidraw render <name>.excalidraw --theme light --scale 3 --max-width 4096 --max-height 4096 --out <name>.png
```

Check what the destination's `width` means: Hugo's figure shortcodes often resize the image to it,
so pass the PNG's own width there; passing the display width blurs the picture.

Then open both PNGs with the Read tool and look at them as the README reader would. Check:
- every label is readable and sits on its own arrow, clear of other lines;
- no arrow passes through a box or crosses another arrow where it could be avoided;
- the eye finds the project box first, and flow reads top to bottom or left to right;
- the dark render reads as well as the light one;
- spacing is even, with no big empty corner.

Adjust the spec and repeat. A pass is a render you look at; 2 to 4 is normal. Stop when a pass
finds nothing a reader would notice.

Layout moves that work:
- An arrow label sits centred on the arrow and hides the line under it. The build wants at least
  25px of visible line on each side. On a vertical arrow a label spreads sideways and covers
  little length, so give the long labels vertical edges and keep horizontal-edge labels short or
  the boxes far apart.
- Once a label is down to 1 word per line, a smaller `wrap` changes nothing: lengthen the arrow
  (move the boxes apart, or split a wide box's note with `\n` so the box narrows) instead.
- A hub (1 box with 4 or more edges): put what starts it above (the reader, schedulers, CI),
  what it touches below, and give the longest label the straight vertical edge. Labels of
  neighbouring diagonal edges meet near the hub, so spread their far ends wide.
- Two arrows between the same pair (a request and its reply): offset them by about half the
  wider label's width plus 10px each way, or merge them into one `both` edge labelled `a / b`.
- An arrow that would cross a box: add a `via` point beside the box.
- Too wide: pull the outer columns in, split long notes with `\n`, reduce a boundary's padding,
  or move a box to a new row.
- A long note (a full path, a command) widens its box and squeezes the arrows beside it. Keep
  notes to a short line and move the detail into the text under the figure.
- A figure that shows taller than wide: put consecutive boxes side by side (a 3-row Z shape fits
  5 boxes), and drop boxes the labels already explain. Shrinking it instead makes the text small
  again.
- Short diagonal arrows in a figure: widen the grid's columns rather than its rows, which
  lengthens them and keeps the figure landscape.

## 5. Put it in the README or page

Put it right after the paragraph that says what the project does, before any status note or the
first `##` heading. Lead in with 1 short plain sentence saying what the picture shows ("How
linkcheck fits around your site:"), not a tour of the arrows, since the picture is the tour. Set
`width` to the PNG width divided by the scale, so it isn't blown up on wide screens:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/overview-dark.png">
  <img alt="<what the diagram shows, in one sentence>" src="docs/diagrams/overview-light.png" width="<px>">
</picture>
```

Paths are relative to the README, so this works on GitHub and in a local markdown viewer. The alt
text is for someone who can't see the image: 1 sentence of about 30 words at most that names the
boxes and the main flow, not every arrow.

For a figure in a page, put the PNG next to the page and keep the spec somewhere that isn't
published: a Hugo page bundle publishes every file in it. Use the site's figure shortcode with a
"Figure N." caption, and introduce the figure in the sentence before it with what it shows. The
light render alone is fine when the site's figures don't switch with the theme.

Replace an older diagram of the same thing rather than adding a second. Tell the user what you
changed, which warnings you fixed, and what you left as it is. Don't commit unless they ask.

## Updating an existing diagram

Run the build with `--check` first. Exit 1 means the `.excalidraw` was edited by hand (for example
on excalidraw.com) since the spec built it. Ask the user whether to keep those edits (then render
the `.excalidraw` as it is and leave the spec alone) or regenerate from the spec and lose them.
