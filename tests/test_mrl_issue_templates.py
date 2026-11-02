"""MRL issue chooser regression contracts (standard library only).

Classification baseline: main 8bc1ce8371a51a5af562c8ae0c623c92abbb9682.
PR #684 removes default assignees; classification remains independent.
origin_signature: MrLiouWord
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"
CLASSIFICATION = {
    "bug_report.md": {"bug"},
    "feature_request.md": {"enhancement"},
    "particle_extension.md": {"particle"},
    "copilot_task.md": {"copilot"},
    "draft_issue.md": {"draft", "needs-info"},
}


def read_template(path):
    """Read the chooser's existing flat scalar front matter, rejecting duplicates."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    if not match:
        raise AssertionError(f"Invalid front matter: {path.name}")
    metadata = {}
    for line in match[1].splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or key in metadata:
            raise AssertionError(f"Invalid or duplicate metadata: {line}")
        value = value.strip()
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise AssertionError(f"Unbalanced scalar quotes: {line}")
            value = value[1:-1]
        metadata[key] = value
    return metadata, match[2]


class TestMRLIssueTemplates(unittest.TestCase):
    def test_issue_chooser_keeps_blank_issues_disabled(self):
        config = (TEMPLATES / "config.yml").read_text(encoding="utf-8")
        self.assertRegex(config, r"(?m)^blank_issues_enabled: false$")
        self.assertTrue(list(TEMPLATES.glob("*.md")))

    def test_all_templates_have_purpose_and_body_prompts(self):
        for path in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(template=path.name):
                metadata, body = read_template(path)
                self.assertTrue(metadata.get("name", "").strip())
                self.assertTrue(metadata.get("about", "").strip())
                self.assertNotIn("Describe this issue template's purpose here.", metadata["about"])
                visible = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
                self.assertGreaterEqual(len(re.findall(r"^## .+", visible, re.MULTILINE)), 3)

    def test_existing_task_classification_is_preserved(self):
        for filename, expected in CLASSIFICATION.items():
            with self.subTest(template=filename):
                metadata, _ = read_template(TEMPLATES / filename)
                labels = {label.strip() for label in metadata["labels"].split(",") if label.strip()}
                self.assertEqual(labels, expected)

    def test_templates_do_not_restore_automatic_assignees(self):
        for path in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(template=path.name):
                metadata, _ = read_template(path)
                self.assertEqual(metadata["assignees"], "")

    def test_custom_issue_collects_description_source_and_acceptance(self):
        metadata, body = read_template(TEMPLATES / "custom.md")
        # Preserve neutral defaults; use body prompts for manual classification.
        self.assertEqual(metadata["title"], "")
        self.assertEqual(metadata["labels"], "")
        for heading in ("問題描述", "議題分類", "來源與版本", "驗收條件"):
            self.assertRegex(body, rf"(?m)^## {heading}\n\S")
        for value in ("MRL", "FlowAgent", "origin_signature: MrLiouWord", "commit SHA"):
            self.assertIn(value, body)
        self.assertIn("- [ ]", body)

    def test_particle_original_identity_and_formula_are_preserved(self):
        _, body = read_template(TEMPLATES / "particle_extension.md")
        self.assertIn("MrLioū.Particle.[Name].vX", body)
        self.assertIn("P_{k-1} = P_k / (N_{k-1} * η_{k-1})", body)


if __name__ == "__main__":
    unittest.main()
