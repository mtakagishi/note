import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.plan_article import PlanInput, plan_article


class PlanArticleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.decision_path = self.root / "decision.json"
        self.packet_path = self.root / "packet.json"
        self.draft_path = self.root / "draft.json"
        self.output_dir = self.root / "plans"
        self.plan_input = PlanInput(
            self.decision_path, self.packet_path, self.draft_path, "2026-08-11T20:00:00Z"
        )
        self._write_decision()
        self._write_packet()
        self._write_plan()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_decision(self, **updates: object) -> None:
        decision = {
            "operation_id": "O-06",
            "run_id": "run-plan",
            "state_after": "CANDIDATE_ACCEPTED",
            "result": "ADVANCE",
        }
        decision.update(updates)
        self.decision_path.write_text(json.dumps(decision), encoding="utf-8")

    def _write_packet(self, **updates: object) -> None:
        packet = {
            "operation_id": "O-05",
            "run_id": "run-plan",
            "state_after": "PACKET_READY",
            "result": "ADVANCE",
            "summary_ja": "運用上の差分を説明できます。",
            "screened_request": {"question_ja": "変更をどう運用するか？"},
            "topics": [{"topic_id": "topic-001", "items": [{"item_id": "item-001"}]}],
            "past_articles": {
                "known_items": [],
                "difference_candidates": [],
                "recheck_items": [],
            },
            "uncertainties": ["対象外の版は未確認です。"],
            "retrieval_failures": [],
        }
        packet.update(updates)
        self.packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    def _write_plan(self, **updates: object) -> None:
        draft = {
            "mode": "PLAN",
            "plan_version": "article-plan-v1",
            "planner_id": "planner-test",
            "working_title_ja": "変更を安全に運用する方法",
            "central_message_ja": "根拠と不確実性を分けると変更を安全に運用できます。",
            "target_readers": ["変更を導入する技術者"],
            "search_intents": ["変更の安全な運用方法を知りたい"],
            "structure_pattern": "TUTORIAL",
            "sections": [
                {
                    "section_id": "section-001",
                    "heading_ja": "変更点を確認する",
                    "purpose_ja": "確認すべき差分を示します。",
                    "reader_takeaway_ja": "差分を根拠まで追跡できます。",
                    "packet_refs": ["topics/topic-001/items/item-001"],
                }
            ],
            "excluded_topics": [
                {"topic_ja": "対象外の版", "reason_ja": "根拠を確認できないためです。"}
            ],
            "uncertainty_treatments": [
                {
                    "packet_ref": "uncertainties/0",
                    "action": "DISCLOSE",
                    "reason_ja": "適用範囲を読者へ明示するためです。",
                }
            ],
        }
        draft.update(updates)
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

    def _write_question(self, questions: list[dict] | None = None) -> None:
        draft = {
            "mode": "AUTHOR_QUESTION",
            "plan_version": "article-plan-v1",
            "planner_id": "planner-test",
            "question_reason_ja": "著者固有の動機を中心メッセージに反映するためです。",
            "questions": questions
            or [
                {
                    "question_id": "question-001",
                    "question_kind": "AUTHOR_MOTIVATION",
                    "question_ja": "この変更を調べたきっかけは何ですか？",
                    "purpose_ja": "記事の中心となる著者の動機を確認します。",
                    "packet_refs": ["screened_request"],
                }
            ],
        }
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

    def test_builds_traceable_article_plan(self) -> None:
        result = plan_article(self.plan_input, self.output_dir)
        saved = json.loads(result.plan_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("PLAN_READY", "ADVANCE"))
        self.assertEqual(saved["required_human_action"], "none")
        self.assertEqual(saved["sections"][0]["packet_refs"], ["topics/topic-001/items/item-001"])

    def test_author_question_holds_and_requests_exception(self) -> None:
        self._write_question()

        result = plan_article(self.plan_input, self.output_dir)
        saved = json.loads(result.plan_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))
        self.assertEqual(saved["required_human_action"], "exception")
        self.assertEqual(len(saved["questions"]), 1)

    def test_rejects_more_than_three_questions(self) -> None:
        question = {
            "question_kind": "AUTHOR_MOTIVATION",
            "question_ja": "動機は何ですか？",
            "purpose_ja": "動機を確認します。",
            "packet_refs": ["screened_request"],
        }
        self._write_question([{**question, "question_id": f"q-{index}"} for index in range(4)])

        with self.assertRaisesRegex(ValueError, "3件以下"):
            plan_article(self.plan_input, self.output_dir)

    def test_rejects_non_author_question(self) -> None:
        self._write_question(
            [
                {
                    "question_id": "question-001",
                    "question_kind": "TECHNICAL_FACT",
                    "question_ja": "仕様を教えてください。",
                    "purpose_ja": "根拠を補います。",
                    "packet_refs": ["screened_request"],
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "AUTHOR_MOTIVATION"):
            plan_article(self.plan_input, self.output_dir)

    def test_question_cannot_be_replaced(self) -> None:
        self._write_question()
        plan_article(self.plan_input, self.output_dir)
        self._write_question(
            [
                {
                    "question_id": "question-002",
                    "question_kind": "AUTHOR_MOTIVATION",
                    "question_ja": "別の動機はありますか？",
                    "purpose_ja": "別の動機を確認します。",
                    "packet_refs": ["screened_request"],
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "一回だけ"):
            plan_article(self.plan_input, self.output_dir)

    def test_plan_after_question_requires_author_context_reference(self) -> None:
        self._write_question()
        plan_article(self.plan_input, self.output_dir)
        self._write_plan()

        with self.assertRaisesRegex(ValueError, "author_context_ref"):
            plan_article(self.plan_input, self.output_dir)

    def test_plan_can_continue_after_public_author_response(self) -> None:
        self._write_question()
        plan_article(self.plan_input, self.output_dir)
        self._write_plan(author_context_ref="issue:2#public-author-response")

        result = plan_article(self.plan_input, self.output_dir)

        self.assertEqual((result.state_after, result.result), ("PLAN_READY", "ADVANCE"))

    def test_requires_treatment_for_every_uncertainty(self) -> None:
        self._write_plan(uncertainty_treatments=[])

        with self.assertRaisesRegex(ValueError, "全不確実性"):
            plan_article(self.plan_input, self.output_dir)

    def test_rejects_unknown_packet_reference(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["sections"][0]["packet_refs"] = ["topics/missing"]
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "存在しないPacket項目"):
            plan_article(self.plan_input, self.output_dir)

    def test_rejects_duplicate_section_id(self) -> None:
        draft = json.loads(self.draft_path.read_text(encoding="utf-8"))
        draft["sections"].append(dict(draft["sections"][0]))
        self.draft_path.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "section_idが重複"):
            plan_article(self.plan_input, self.output_dir)

    def test_rejects_mismatched_run_id(self) -> None:
        self._write_decision(run_id="another-run")

        with self.assertRaisesRegex(ValueError, "run_idが一致"):
            plan_article(self.plan_input, self.output_dir)

    def test_rejects_non_accepted_candidate(self) -> None:
        self._write_decision(state_after="HOLD", result="HOLD")

        with self.assertRaisesRegex(ValueError, "CANDIDATE_ACCEPTED / ADVANCE"):
            plan_article(self.plan_input, self.output_dir)

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = plan_article(self.plan_input, self.output_dir)
        first_mtime = first.plan_path.stat().st_mtime_ns

        second = plan_article(self.plan_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.plan_path.stat().st_mtime_ns, first_mtime)


if __name__ == "__main__":
    unittest.main()
