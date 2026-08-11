import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.build_evidence_packet import (
    PacketInput,
    build_evidence_packet,
)


class BuildEvidencePacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.evidence_path = self.root / "evidence.json"
        self.draft_path = self.root / "draft.json"
        self.output_dir = self.root / "packets"
        self.packet_input = PacketInput(
            self.evidence_path,
            self.draft_path,
            "2026-08-11T12:00:00Z",
        )
        self._write_evidence()
        self._write_draft()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_evidence(self, **updates: object) -> None:
        evidence = {
            "schema_version": 1,
            "operation_id": "O-04",
            "run_id": "run-packet",
            "state_after": "EVIDENCE_READY",
            "result": "ADVANCE",
            "screened_request": {"question_ja": "根拠を整理するには？"},
            "uncertainties": ["対象バージョンの一部が不明です。"],
            "retrieval_failures": [{"url": "https://missing.example", "reason": "HTTP 404"}],
            "metrics": {"adopted_sources": 3},
            "evidence": [
                {
                    "source_id": "source-001",
                    "source_type": "primary",
                    "url": "https://official.example/spec",
                    "final_url": "https://official.example/spec",
                    "metadata": {"title": "公式仕様"},
                },
                {
                    "source_id": "source-002",
                    "source_type": "secondary",
                    "url": "https://article.example/review",
                    "final_url": "https://article.example/review",
                    "metadata": {"title": "解説"},
                },
                {
                    "source_id": "source-003",
                    "source_type": "community",
                    "url": "https://community.example/topic",
                    "final_url": "https://community.example/topic",
                    "metadata": {"title": "利用者の反応"},
                },
            ],
        }
        evidence.update(updates)
        self.evidence_path.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")

    def _write_draft(self, **updates: object) -> None:
        draft = {
            "summary_ja": "取得済み根拠を論点別に整理しました。",
            "topics": [
                {
                    "topic_id": "topic-001",
                    "title_ja": "仕様と評価",
                    "items": [
                        {
                            "item_id": "item-fact",
                            "kind": "fact",
                            "statement_ja": "公式仕様に機能が記載されています。",
                            "source_ids": ["source-001"],
                        },
                        {
                            "item_id": "item-reaction",
                            "kind": "community_reaction",
                            "statement_ja": "利用者から異なる評価があります。",
                            "source_ids": ["source-002", "source-003"],
                        },
                        {
                            "item_id": "item-conflict",
                            "kind": "contradiction",
                            "statement_ja": "公式仕様と利用者報告に差があります。",
                            "source_ids": ["source-001", "source-003"],
                        },
                    ],
                }
            ],
            "past_articles": {
                "article_refs": ["blog:2026-example"],
                "known_items": [],
                "difference_candidates": [
                    {
                        "item_id": "item-difference",
                        "kind": "inference",
                        "statement_ja": "過去記事以降に仕様が追加された可能性があります。",
                        "source_ids": ["source-001"],
                    }
                ],
                "recheck_items": [],
            },
        }
        draft.update(updates)
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

    def test_builds_traceable_packet_and_inherits_uncertainty(self) -> None:
        result = build_evidence_packet(self.packet_input, self.output_dir)
        saved = json.loads(result.packet_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("PACKET_READY", "ADVANCE"))
        self.assertEqual(saved["producer"], "skill_agent")
        self.assertEqual(saved["topics"][0]["items"][0]["source_types"], ["primary"])
        self.assertEqual(saved["past_articles"]["status"], "COMPARED")
        self.assertEqual(saved["uncertainties"], ["対象バージョンの一部が不明です。"])
        self.assertEqual(saved["retrieval_failures"][0]["reason"], "HTTP 404")

    def test_rejects_unknown_source_id(self) -> None:
        self._write_draft(
            topics=[
                {
                    "topic_id": "topic-001",
                    "title_ja": "不正な参照",
                    "items": [
                        {
                            "item_id": "item-001",
                            "kind": "fact",
                            "statement_ja": "存在しない根拠です。",
                            "source_ids": ["source-999"],
                        }
                    ],
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "存在しないsource_id"):
            build_evidence_packet(self.packet_input, self.output_dir)

    def test_rejects_empty_statement(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["topics"][0]["items"][0]["statement_ja"] = " "
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "空でない文字列"):
            build_evidence_packet(self.packet_input, self.output_dir)

    def test_contradiction_requires_two_sources(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["topics"][0]["items"][2]["source_ids"] = ["source-001"]
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "二件以上"):
            build_evidence_packet(self.packet_input, self.output_dir)

    def test_community_reaction_requires_non_primary_source(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["topics"][0]["items"][1]["source_ids"] = ["source-001"]
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "secondaryまたはcommunity"):
            build_evidence_packet(self.packet_input, self.output_dir)

    def test_does_not_infer_difference_without_past_article(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["past_articles"]["article_refs"] = []
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "過去記事参照なし"):
            build_evidence_packet(self.packet_input, self.output_dir)

    def test_without_past_article_marks_difference_unconfirmed(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["past_articles"] = {
            "article_refs": [],
            "known_items": [],
            "difference_candidates": [],
            "recheck_items": [],
        }
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        result = build_evidence_packet(self.packet_input, self.output_dir)
        saved = json.loads(result.packet_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["past_articles"]["status"], "UNCONFIRMED_NO_PAST_ARTICLE")

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = build_evidence_packet(self.packet_input, self.output_dir)
        first_mtime = first.packet_path.stat().st_mtime_ns

        second = build_evidence_packet(self.packet_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.packet_path.stat().st_mtime_ns, first_mtime)

    def test_rejects_non_advanced_evidence_set(self) -> None:
        self._write_evidence(result="HOLD")

        with self.assertRaisesRegex(ValueError, "EVIDENCE_READY / ADVANCE"):
            build_evidence_packet(self.packet_input, self.output_dir)


if __name__ == "__main__":
    unittest.main()
