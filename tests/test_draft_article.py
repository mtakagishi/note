import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.draft_article import DraftInput, draft_article


class DraftArticleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.plan_path = self.root / "plan.json"
        self.packet_path = self.root / "packet.json"
        self.proposal_path = self.root / "proposal.json"
        self.output_dir = self.root / "drafts"
        self.draft_input = DraftInput(
            self.plan_path, self.packet_path, self.proposal_path, "2026-08-11T22:00:00Z"
        )
        self._write_plan()
        self._write_packet()
        self._write_proposal()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_plan(self, **updates: object) -> None:
        plan = {
            "operation_id": "O-07",
            "run_id": "run-draft",
            "state_after": "PLAN_READY",
            "result": "ADVANCE",
            "working_title_ja": "変更を安全に運用する方法",
            "central_message_ja": "根拠と不確実性を分けます。",
            "sections": [
                {
                    "section_id": "section-001",
                    "heading_ja": "変更点を確認する",
                    "packet_refs": ["topics/topic-001/items/item-001", "uncertainties/0"],
                },
                {
                    "section_id": "section-002",
                    "heading_ja": "適用範囲を限定する",
                    "packet_refs": ["topics/topic-001/items/item-002", "uncertainties/1"],
                },
            ],
            "uncertainty_treatments": [
                {"packet_ref": "uncertainties/0", "action": "DISCLOSE"},
                {"packet_ref": "uncertainties/1", "action": "EXCLUDE"},
            ],
        }
        plan.update(updates)
        self.plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    def _write_packet(self, **updates: object) -> None:
        packet = {
            "operation_id": "O-05",
            "run_id": "run-draft",
            "state_after": "PACKET_READY",
            "result": "ADVANCE",
            "created_at": "2026-08-11T18:00:00Z",
            "topics": [
                {
                    "topic_id": "topic-001",
                    "items": [{"item_id": "item-001"}, {"item_id": "item-002"}],
                }
            ],
            "past_articles": {},
            "uncertainties": ["版の一部が未確認です。", "対象外の版です。"],
            "source_catalog": [{"source_id": "source-001", "target_version": "2.0"}],
        }
        packet.update(updates)
        self.packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    def _write_proposal(self, **updates: object) -> None:
        proposal = {
            "draft_version": "article-draft-v1",
            "drafter_id": "drafter-test",
            "sections": [
                {
                    "section_id": "section-001",
                    "blocks": [
                        {
                            "block_id": "block-001",
                            "body_rst": "公式情報で確認できる変更点を説明します。",
                            "packet_refs": ["topics/topic-001/items/item-001"],
                        },
                        {
                            "block_id": "block-002",
                            "body_rst": "対象バージョンの一部は未確認です。",
                            "packet_refs": ["uncertainties/0"],
                        },
                    ],
                },
                {
                    "section_id": "section-002",
                    "blocks": [
                        {
                            "block_id": "block-003",
                            "body_rst": "確認済みの適用範囲だけを説明します。",
                            "packet_refs": ["topics/topic-001/items/item-002"],
                        }
                    ],
                },
            ],
        }
        proposal.update(updates)
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

    def _proposal(self) -> dict:
        return json.loads(self.proposal_path.read_text(encoding="utf-8"))

    def test_builds_rst_and_traceable_manifest(self) -> None:
        result = draft_article(self.draft_input, self.output_dir)
        draft = result.draft_path.read_text(encoding="utf-8")
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("DRAFT_READY", "ADVANCE"))
        self.assertIn(":公開日: 未確定", draft)
        self.assertIn(":対象バージョン: 2.0", draft)
        self.assertNotIn(".. post::", draft)
        self.assertEqual(manifest["sections"][0]["blocks"][0]["packet_refs"], ["topics/topic-001/items/item-001"])
        self.assertEqual(len(manifest["sections"][0]["blocks"][0]["sha256"]), 64)

    def test_rejects_wrong_section_order(self) -> None:
        proposal = self._proposal()
        proposal["sections"].reverse()
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "同じIDと順序"):
            draft_article(self.draft_input, self.output_dir)

    def test_rejects_plan_external_reference(self) -> None:
        proposal = self._proposal()
        proposal["sections"][0]["blocks"][0]["packet_refs"] = ["topics/missing"]
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "Plan外"):
            draft_article(self.draft_input, self.output_dir)

    def test_requires_every_planned_reference_except_excluded_uncertainty(self) -> None:
        proposal = self._proposal()
        proposal["sections"][0]["blocks"] = proposal["sections"][0]["blocks"][:1]
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "不確実性を本文"):
            draft_article(self.draft_input, self.output_dir)

    def test_rejects_excluded_uncertainty_reference(self) -> None:
        proposal = self._proposal()
        proposal["sections"][1]["blocks"][0]["packet_refs"].append("uncertainties/1")
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "EXCLUDE"):
            draft_article(self.draft_input, self.output_dir)

    def test_rejects_duplicate_block_id(self) -> None:
        proposal = self._proposal()
        proposal["sections"][1]["blocks"][0]["block_id"] = "block-001"
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "block_idが重複"):
            draft_article(self.draft_input, self.output_dir)

    def test_rejects_empty_body(self) -> None:
        proposal = self._proposal()
        proposal["sections"][0]["blocks"][0]["body_rst"] = " "
        self.proposal_path.write_text(json.dumps(proposal, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "空でない文字列"):
            draft_article(self.draft_input, self.output_dir)

    def test_rejects_unsafe_directives(self) -> None:
        for directive in ("raw", "include", "literalinclude", "image", "figure", "post"):
            with self.subTest(directive=directive):
                self._write_proposal()
                proposal = self._proposal()
                proposal["sections"][0]["blocks"][0]["body_rst"] = f".. {directive}:: value"
                self.proposal_path.write_text(
                    json.dumps(proposal, ensure_ascii=False), encoding="utf-8"
                )
                with self.assertRaisesRegex(ValueError, "許可されない"):
                    draft_article(self.draft_input, self.output_dir)

    def test_rejects_non_ready_plan(self) -> None:
        self._write_plan(state_after="HOLD", result="HOLD")

        with self.assertRaisesRegex(ValueError, "PLAN_READY / ADVANCE"):
            draft_article(self.draft_input, self.output_dir)

    def test_rejects_mismatched_run_id(self) -> None:
        self._write_packet(run_id="another-run")

        with self.assertRaisesRegex(ValueError, "run_idが一致"):
            draft_article(self.draft_input, self.output_dir)

    def test_does_not_write_to_publication_directory(self) -> None:
        publication_dir = Path.cwd() / "docs" / "blog" / "posts"

        with self.assertRaisesRegex(ValueError, "docs/blog/posts"):
            draft_article(self.draft_input, publication_dir)

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = draft_article(self.draft_input, self.output_dir)
        draft_mtime = first.draft_path.stat().st_mtime_ns
        manifest_mtime = first.manifest_path.stat().st_mtime_ns

        second = draft_article(self.draft_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.draft_path.stat().st_mtime_ns, draft_mtime)
        self.assertEqual(second.manifest_path.stat().st_mtime_ns, manifest_mtime)


if __name__ == "__main__":
    unittest.main()
