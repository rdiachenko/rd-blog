#!/usr/bin/env python3
"""Build an Excalidraw scene from a small layout spec (JSON).

    build_scene.py SPEC.json OUT.excalidraw          write the scene
    build_scene.py SPEC.json OUT.excalidraw --check  exit 1 if OUT differs from what SPEC builds

The output is deterministic: the same spec always gives byte-identical JSON, so `--check` tells a
hand-edited scene apart from a generated one. Stdlib only.
"""

import hashlib
import json
import math
import sys
import textwrap

KINDS = {
    # kind: (stroke, background); Excalidraw's own palette, which its dark theme inverts cleanly
    "system": ("#1971c2", "#a5d8ff"),
    "person": ("#6741d9", "#d0bfff"),
    "external": ("#495057", "#e9ecef"),
    "store": ("#e8590c", "#ffec99"),
    "trigger": ("#2f9e44", "#b2f2bb"),
    "plain": ("#1e1e1e", "transparent"),
}
FONTS = {"hand": 5, "normal": 6, "code": 8}  # Excalifont, Nunito, Comic Shanns
CHAR_W = {5: 0.56, 6: 0.55, 8: 0.6}  # average glyph width / font size, measured on renders
LINE_H = 1.25


def die(msg: str) -> None:
    print(f"build_scene: {msg}", file=sys.stderr)
    sys.exit(2)


def seed(*parts) -> int:
    return int(hashlib.sha256("/".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def base(eid: str, kind: str, x: float, y: float, w: float, h: float, **kw) -> dict:
    el = {
        "id": eid,
        "type": kind,
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(w, 2),
        "height": round(h, 2),
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": seed(eid, "seed"),
        "version": 1,
        "versionNonce": seed(eid, "nonce"),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }
    el.update(kw)
    return el


def text_size(text: str, size: int, family: int) -> tuple[float, float]:
    lines = text.split("\n")
    return max(len(line) for line in lines) * size * CHAR_W[family], len(lines) * size * LINE_H


def text_el(eid, text, x, y, size, family, container=None, color="#1e1e1e", align="center"):
    w, h = text_size(text, size, family)
    return base(
        eid,
        "text",
        x - w / 2 if align == "center" else x,
        y - h / 2,
        w,
        h,
        strokeColor=color,
        text=text,
        originalText=text,
        fontSize=size,
        fontFamily=family,
        textAlign=align,
        verticalAlign="middle",
        containerId=container,
        autoResize=True,
        lineHeight=LINE_H,
    )


def wrap(label: str, width: int) -> str:
    return "\n".join("\n".join(textwrap.wrap(part, width) or [""]) for part in label.split("\n"))


def clip(cx, cy, w, h, tx, ty, gap, ellipse=False):
    """The point where the ray from a box's centre towards (tx, ty) leaves the box, plus gap."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    if ellipse:
        a, b = w / 2 + gap, h / 2 + gap
        s = 1 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
        return cx + dx * s, cy + dy * s
    sx = (w / 2 + gap) / abs(dx) if dx else math.inf
    sy = (h / 2 + gap) / abs(dy) if dy else math.inf
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def build(spec: dict) -> dict:
    grid = spec.get("grid", {})
    col_w, row_h = grid.get("col", 300), grid.get("row", 170)
    family = FONTS.get(spec.get("font", "hand")) or die("font must be hand, normal or code")
    size = spec.get("fontSize", 20)
    edge_size = spec.get("edgeFontSize", 16)
    rough = 1 if spec.get("font", "hand") == "hand" else 0
    elements, boxes = [], {}

    for b in spec.get("boundaries", []):
        missing = [n for n in b["nodes"] if n not in {x["id"] for x in spec["nodes"]}]
        if missing:
            die(f"boundary {b['label']!r} names unknown nodes {missing}")

    for n in spec["nodes"]:
        nid = n["id"]
        if nid in boxes:
            die(f"duplicate node id {nid!r}")
        kind = n.get("kind", "plain")
        if kind not in KINDS:
            die(f"node {nid!r}: kind must be one of {', '.join(KINDS)}")
        stroke, fill = KINDS[kind]
        note, note_size = n.get("note"), round(size * 0.75)
        tw, th = text_size(n["label"], size, family)
        nw, nh = text_size(note, note_size, family) if note else (0, 0)
        gap = 6 if note else 0
        w = n.get("w", max(160, tw + 48, nw + 48))
        h = n.get("h", max(70, th + gap + nh + 36))
        cx, cy = n["col"] * col_w, n["row"] * row_h
        shape = "ellipse" if kind == "person" else "rectangle"
        box = base(
            nid,
            shape,
            cx - w / 2,
            cy - h / 2,
            w,
            h,
            strokeColor=stroke,
            backgroundColor=fill,
            roughness=rough,
            roundness={"type": 3} if shape == "rectangle" else {"type": 2},
            strokeWidth=3 if kind == "system" else 2,
        )
        boxes[nid] = (cx, cy, w, h, box, shape == "ellipse")
        if not note:  # bound text: stays centred when the box is edited on excalidraw.com
            txt = text_el(f"{nid}-text", n["label"], cx, cy, size, family, container=nid)
            box["boundElements"].append({"type": "text", "id": txt["id"]})
            elements += [box, txt]
            continue
        # title and a smaller grey note: free text grouped with the box, so they move together
        top = cy - (th + gap + nh) / 2
        group = [f"{nid}-group"]
        box["groupIds"] = group
        title = text_el(f"{nid}-text", n["label"], cx, top + th / 2, size, family)
        sub = text_el(
            f"{nid}-note", note, cx, top + th + gap + nh / 2, note_size, family, color="#495057"
        )
        title["groupIds"] = sub["groupIds"] = group
        elements += [box, title, sub]

    for i, b in enumerate(spec.get("boundaries", [])):
        pad = b.get("padding", 40)
        xs = [boxes[n][0] - boxes[n][2] / 2 for n in b["nodes"]]
        xe = [boxes[n][0] + boxes[n][2] / 2 for n in b["nodes"]]
        ys = [boxes[n][1] - boxes[n][3] / 2 for n in b["nodes"]]
        ye = [boxes[n][1] + boxes[n][3] / 2 for n in b["nodes"]]
        x0, y0 = min(xs) - pad, min(ys) - pad - edge_size * 1.6
        x1, y1 = max(xe) + pad, max(ye) + pad
        bid = f"boundary-{i}"
        elements.insert(
            0,
            base(
                bid,
                "rectangle",
                x0,
                y0,
                x1 - x0,
                y1 - y0,
                strokeColor="#868e96",
                strokeStyle="dashed",
                roughness=rough,
                roundness={"type": 3},
                strokeWidth=1,
            ),
        )
        lw, lh = text_size(b["label"], edge_size, family)
        elements.insert(
            1,
            text_el(
                f"{bid}-text",
                b["label"],
                x0 + 14,
                y0 + 10 + lh / 2,
                edge_size,
                family,
                color="#868e96",
                align="left",
            ),
        )

    for i, e in enumerate(spec.get("edges", [])):
        for end in ("from", "to"):
            if e[end] not in boxes:
                die(f"edge {i}: unknown node {e[end]!r}")
        a, b = boxes[e["from"]], boxes[e["to"]]
        via = [(c * col_w, r * row_h) for c, r in e.get("via", [])]
        off = e.get("offset", 0)
        first, last = (via[0] if via else (b[0], b[1])), (via[-1] if via else (a[0], a[1]))
        sx, sy = clip(a[0], a[1], a[2], a[3], *first, 8, a[5])
        tx, ty = clip(b[0], b[1], b[2], b[3], *last, 8, b[5])
        if off:  # shift a straight edge sideways so a pair of opposite edges don't overlap
            dx, dy = tx - sx, ty - sy
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln * off, dx / ln * off
            sx, sy, tx, ty = sx + nx, sy + ny, tx + nx, ty + ny
        pts = [(sx, sy), *via, (tx, ty)]
        eid = f"edge-{i}-{e['from']}-{e['to']}"
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        arrow = base(
            eid,
            "arrow",
            sx,
            sy,
            max(xs) - min(xs),
            max(ys) - min(ys),
            strokeColor=e.get("color", "#1e1e1e"),
            roughness=rough,
            strokeStyle="dashed" if e.get("dashed") else "solid",
            roundness={"type": 2} if via else None,
            points=[[round(px - sx, 2), round(py - sy, 2)] for px, py in pts],
            lastCommittedPoint=None,
            startBinding={"elementId": e["from"], "focus": 0, "gap": 8},
            endBinding={"elementId": e["to"], "focus": 0, "gap": 8},
            startArrowhead="arrow" if e.get("both") else None,
            endArrowhead="arrow",
            elbowed=False,
        )
        a[4]["boundElements"].append({"type": "arrow", "id": eid})
        b[4]["boundElements"].append({"type": "arrow", "id": eid})
        elements.append(arrow)
        if e.get("label"):
            seg = len(pts) // 2
            (x1, y1), (x2, y2) = pts[seg - 1], pts[seg]
            label = wrap(e["label"], e.get("wrap", 26))
            txt = text_el(
                f"{eid}-text", label, (x1 + x2) / 2, (y1 + y2) / 2, edge_size, family, container=eid
            )
            arrow["boundElements"].append({"type": "text", "id": txt["id"]})
            elements.append(txt)

    for note in spec.get("notes", []):
        nid = f"note-{note['id']}"
        elements.append(
            text_el(
                nid,
                note["text"],
                note["col"] * col_w,
                note["row"] * row_h,
                note.get("fontSize", edge_size),
                family,
                color="#495057",
                align="center",
            )
        )

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "readme-diagram",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20, "exportBackground": True},
        "files": {},
    }


def bbox(el: dict, pad: float = 0) -> tuple[float, float, float, float]:
    return el["x"] - pad, el["y"] - pad, el["x"] + el["width"] + pad, el["y"] + el["height"] + pad


def hits(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def seg_hits_box(p, q, box) -> bool:
    """Whether segment p-q passes through box (sampled; good enough for a layout warning)."""
    return any(
        box[0] < p[0] + (q[0] - p[0]) * t < box[2] and box[1] < p[1] + (q[1] - p[1]) * t < box[3]
        for t in (i / 40 for i in range(1, 40))
    )


def layout_warnings(scene: dict) -> list[str]:
    """Collisions a reader would notice: labels on labels, labels on boxes, arrows through boxes."""
    els = {e["id"]: e for e in scene["elements"]}
    boxes = [
        e
        for e in els.values()
        if e["type"] in ("rectangle", "ellipse") and not e["id"].startswith("boundary-")
    ]
    labels = [
        e
        for e in els.values()
        if e["type"] == "text" and (e["containerId"] or "").startswith("edge-")
    ]
    notes = [e for e in els.values() if e["id"].startswith("note-")]
    titles = [e for e in els.values() if e["type"] == "text" and e["id"].startswith("boundary-")]
    frames = [
        e for e in els.values() if e["type"] == "rectangle" and e["id"].startswith("boundary-")
    ]

    def frame_sides(f):
        x0, y0, x1, y1 = bbox(f)
        return [
            (x0 - 2, y0, x0 + 2, y1),
            (x1 - 2, y0, x1 + 2, y1),
            (x0, y0 - 2, x1, y0 + 2),
            (x0, y1 - 2, x1, y1 + 2),
        ]

    def frame_title(f):
        return els[f"{f['id']}-text"]["text"]

    out = []
    for i, a in enumerate(labels):
        name = "label " + repr(a["text"].replace("\n", " "))
        for b in labels[i + 1 :] + titles + notes:
            if hits(bbox(a, 6), bbox(b, 6)):
                out.append(f"{name} overlaps " + repr(b["text"].replace("\n", " ")))
        for box in boxes:
            if hits(bbox(a, 6), bbox(box)):
                out.append(f"{name} overlaps box {box['id']!r}")
        arrow = els[a["containerId"]]
        pts = arrow["points"]
        length = sum(math.dist(p, q) for p, q in zip(pts, pts[1:], strict=False))
        # how much line the label covers: its box projected onto the arrow's overall direction
        ux, uy = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
        un = math.hypot(ux, uy) or 1
        span = a["width"] * abs(ux) / un + a["height"] * abs(uy) / un
        if span + 50 > length:  # under ~25px of line each side, the arrow reads as a stub
            out.append(
                f"{name} leaves too little arrow ({span:.0f}px label on {length:.0f}px): "
                "move the boxes apart or shorten or wrap the label"
            )
        for frame in frames:
            if any(hits(bbox(a, 4), side) for side in frame_sides(frame)):
                out.append(
                    f"{name} sits on the boundary line of {frame_title(frame)!r}: "
                    "move it, or change the boundary's padding"
                )
    for arrow in (e for e in els.values() if e["type"] == "arrow"):
        ends = {arrow["startBinding"]["elementId"], arrow["endBinding"]["elementId"]}
        abs_pts = [(arrow["x"] + px, arrow["y"] + py) for px, py in arrow["points"]]
        for box in boxes:
            if box["id"] not in ends and any(
                seg_hits_box(p, q, bbox(box)) for p, q in zip(abs_pts, abs_pts[1:], strict=False)
            ):
                out.append(f"arrow {arrow['id']} crosses box {box['id']!r}: add a via point")
        for t in titles + notes:
            if any(
                seg_hits_box(p, q, bbox(t, 4)) for p, q in zip(abs_pts, abs_pts[1:], strict=False)
            ):
                what = "the boundary title" if t in titles else "the note"
                out.append(f"arrow {arrow['id']} crosses {what} {t['text']!r}")
    for n in notes:
        for box in boxes:
            if hits(bbox(n, 6), bbox(box)):
                out.append(f"note {n['text']!r} overlaps box {box['id']!r}")
    return out


def png_size(scene: dict, scale: int = 2, padding: int = 20) -> tuple[int, int]:
    """The size `excalidraw render --scale <scale>` gives this scene (estimated text widths)."""
    xs, ys = [], []
    for e in scene["elements"]:
        if e["type"] == "arrow":
            xs += [e["x"] + px for px, _ in e["points"]]
            ys += [e["y"] + py for _, py in e["points"]]
        else:
            x0, y0, x1, y1 = bbox(e)
            xs += [x0, x1]
            ys += [y0, y1]
    return (
        round((max(xs) - min(xs) + 2 * padding) * scale),
        round((max(ys) - min(ys) + 2 * padding) * scale),
    )


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--check"]
    if len(args) != 2:
        die("usage: build_scene.py SPEC.json OUT.excalidraw [--check]")
    try:
        spec = json.load(open(args[0], encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"can't read {args[0]}: {exc}")
    scene = build(spec)
    out = json.dumps(scene, indent=2, ensure_ascii=False) + "\n"
    for w in layout_warnings(scene):
        print(f"layout: {w}", file=sys.stderr)
    pw, ph = png_size(scene)
    if pw > 1800:
        print(
            f"layout: about {pw}px wide at --scale 2, over the README's 1800: "
            "move a box to a new row or pull the columns in",
            file=sys.stderr,
        )
    if "--check" in sys.argv:
        try:
            same = open(args[1], encoding="utf-8").read() == out
        except OSError:
            same = False
        print("matches the spec" if same else f"{args[1]} differs from what the spec builds")
        sys.exit(0 if same else 1)
    with open(args[1], "w", encoding="utf-8") as f:
        f.write(out)
    print(
        f"wrote {args[1]}: {len(spec['nodes'])} nodes, {len(spec.get('edges', []))} edges, "
        f"about {pw}x{ph}px at --scale 2"
    )


if __name__ == "__main__":
    main()
