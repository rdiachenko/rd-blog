"""Tests for build_scene.py. Stdlib only: python3 -m unittest discover -s tests"""

import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "readme-diagram" / "scripts" / "build_scene.py"
EXAMPLE = ROOT / "example" / "blog.json"

spec = importlib.util.spec_from_file_location("build_scene", SCRIPT)
build_scene = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_scene)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def scene_for(spec_dict: dict) -> dict:
    return build_scene.build(spec_dict)


class ExampleTest(unittest.TestCase):
    def test_committed_scene_matches_the_spec(self):
        result = run(str(EXAMPLE), str(EXAMPLE.with_suffix(".excalidraw")), "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_example_builds_without_layout_warnings(self):
        scene = scene_for(json.loads(EXAMPLE.read_text("utf-8")))
        self.assertEqual(build_scene.layout_warnings(scene), [])

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp, "a.excalidraw"), Path(tmp, "b.excalidraw")
            run(str(EXAMPLE), str(a))
            run(str(EXAMPLE), str(b))
            self.assertEqual(a.read_bytes(), b.read_bytes())


class LayoutWarningTest(unittest.TestCase):
    def test_overlapping_labels_are_reported(self):
        spec = {
            "nodes": [
                {"id": "a", "label": "A", "col": 0, "row": 0},
                {"id": "b", "label": "B", "col": 0, "row": 1},
            ],
            "edges": [
                {"from": "a", "to": "b", "label": "a long request label"},
                {"from": "b", "to": "a", "label": "a long reply label"},
            ],
        }
        warnings = build_scene.layout_warnings(scene_for(spec))
        self.assertTrue(any("overlaps" in w for w in warnings), warnings)

    def test_arrow_through_a_box_is_reported(self):
        spec = {
            "nodes": [
                {"id": "a", "label": "A", "col": 0, "row": 0},
                {"id": "mid", "label": "Middle", "col": 1, "row": 0},
                {"id": "b", "label": "B", "col": 2, "row": 0},
            ],
            "edges": [{"from": "a", "to": "b"}],
        }
        warnings = build_scene.layout_warnings(scene_for(spec))
        self.assertTrue(any("crosses box 'mid'" in w for w in warnings), warnings)

    def test_arrow_from_an_ellipse_starts_on_its_outline(self):
        spec = {
            "nodes": [
                {"id": "you", "label": "You", "kind": "person", "col": 0, "row": 0},
                {"id": "app", "label": "App", "col": 1, "row": 1},
            ],
            "edges": [{"from": "you", "to": "app"}],
        }
        els = {e["id"]: e for e in scene_for(spec)["elements"]}
        you, arrow = els["you"], els["edge-0-you-app"]
        cx, cy = you["x"] + you["width"] / 2, you["y"] + you["height"] / 2
        a, b = you["width"] / 2 + 8, you["height"] / 2 + 8  # outline plus the binding gap
        value = ((arrow["x"] - cx) / a) ** 2 + ((arrow["y"] - cy) / b) ** 2
        self.assertTrue(math.isclose(value, 1, abs_tol=0.01), value)


class DecisionTest(unittest.TestCase):
    SPEC = {
        "nodes": [
            {"id": "q", "label": "Is v0 a\nrelease tag?", "kind": "decision", "col": 1, "row": 0},
            {"id": "yes", "label": "Download", "col": 0, "row": 1.2},
        ],
        "edges": [{"from": "q", "to": "yes", "label": "yes"}],
    }

    def test_decision_is_a_diamond_that_fits_its_text(self):
        els = {e["id"]: e for e in scene_for(self.SPEC)["elements"]}
        q, text = els["q"], els["q-text"]
        self.assertEqual(q["type"], "diamond")
        # a centred box fits a diamond when its width and height shares sum to at most 1
        fit = text["width"] / q["width"] + text["height"] / q["height"]
        self.assertLessEqual(fit, 1, fit)

    def test_arrow_from_a_diamond_starts_on_its_outline(self):
        els = {e["id"]: e for e in scene_for(self.SPEC)["elements"]}
        q, arrow = els["q"], els["edge-0-q-yes"]
        cx, cy = q["x"] + q["width"] / 2, q["y"] + q["height"] / 2
        a, b = q["width"] / 2 + 8, q["height"] / 2 + 8  # outline plus the binding gap
        value = abs(arrow["x"] - cx) / a + abs(arrow["y"] - cy) / b
        self.assertTrue(math.isclose(value, 1, abs_tol=0.01), value)


class ColumnTest(unittest.TestCase):
    """A figure a page shrinks into its text column: report text size and height."""

    def test_wide_layout_with_large_text_passes(self):
        spec = {
            "nodes": [
                {"id": "a", "label": "Your workflow", "note": "uses: owner/repo@v0",
                 "col": 0, "row": 0},
                {"id": "b", "label": "GitHub runner", "note": "copies the action",
                 "col": 2, "row": 0},
            ],
            "edges": [{"from": "a", "to": "b", "label": "starts the job"}],
            "column": 700, "fontSize": 28, "edgeFontSize": 24, "grid": {"col": 330, "row": 230},
        }
        summary, warnings = build_scene.column_report(scene_for(spec), spec)
        self.assertEqual(warnings, [])
        self.assertIn("in a 700px column", summary)

    def test_small_text_is_reported(self):
        spec = {
            "nodes": [
                {"id": f"n{i}", "label": "A rather long box title", "col": i * 2, "row": 0}
                for i in range(3)
            ],
            "column": 700,
        }
        _, warnings = build_scene.column_report(scene_for(spec), spec)
        self.assertTrue(any("smallest text" in w for w in warnings), warnings)

    def test_tall_figure_is_reported(self):
        spec = {
            "nodes": [
                {"id": f"n{i}", "label": f"Step {i}", "note": "a short note", "col": 0, "row": i}
                for i in range(5)
            ],
            "edges": [{"from": f"n{i}", "to": f"n{i + 1}"} for i in range(4)],
            "column": 700, "fontSize": 28, "edgeFontSize": 24, "grid": {"col": 300, "row": 200},
        }
        _, warnings = build_scene.column_report(scene_for(spec), spec)
        self.assertTrue(any("taller than wide" in w for w in warnings), warnings)

    def test_column_skips_the_readme_width_limit(self):
        spec = {
            "nodes": [{"id": f"n{i}", "label": f"Box {i}", "col": i, "row": 0} for i in range(8)],
            "column": 700,
        }
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp, "wide.json")
            src.write_text(json.dumps(spec))
            figure = run(str(src), str(Path(tmp, "wide.excalidraw")))
            src.write_text(json.dumps({k: v for k, v in spec.items() if k != "column"}))
            readme = run(str(src), str(Path(tmp, "wide.excalidraw")))
        self.assertNotIn("over the README's 1800", figure.stderr)
        self.assertIn("over the README's 1800", readme.stderr)


class ErrorTest(unittest.TestCase):
    def test_unknown_kind_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp, "bad.json")
            bad.write_text(
                json.dumps(
                    {"nodes": [{"id": "x", "label": "X", "kind": "cloud", "col": 0, "row": 0}]}
                )
            )
            result = run(str(bad), str(Path(tmp, "out.excalidraw")))
        self.assertEqual(result.returncode, 2)
        self.assertIn("kind must be one of", result.stderr)

    def test_check_fails_on_a_hand_edited_scene(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp, "blog.excalidraw")
            run(str(EXAMPLE), str(out))
            out.write_text(out.read_text().replace('"Readers"', '"Visitors"', 1))
            result = run(str(EXAMPLE), str(out), "--check")
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
