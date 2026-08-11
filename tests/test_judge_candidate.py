import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.judge_candidate import JudgeInput, judge_candidate


class JudgeCandidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.packet_path = self.root / "packet.json"
        self.judgment_path = self.root / "judgment.json"
        self.output_dir = self.root / "decisions"
        self.judge_input = JudgeInput(
            self.packet_path, self.judgment_path, "2026-08-11T18:00:00Z"
        )
        self._write_packet()
        self._write_judgment()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write_packet(self, **updates: object) -> None:
        packet = {
            "operation_id": "O-05",
            "run_id": "run-judge",
            "state_after": "PACKET_READY",
            "result": "ADVANCE",
            "summary_ja": "再利用可能な差分があります。",
            "screened_request": {"question_ja": "この変更をどう運用するか？"},
            "topics": [{"topic_id": "topic-001", "items": [{"item_id": "item-001"}]}],
            "past_articles": {
                "status": "COMPARED",
                "known_items": [],
                "difference_candidates": [{"item_id": "difference-001"}],
                "recheck_items": [],
            },
            "uncertainties": ["対象外の版は未確認です。"],
            "retrieval_failures": [],
        }
        packet.update(updates)
        self.packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    def _write_judgment(self, **evaluation_updates: object) -> None:
        evaluations = {
            "evidence_sufficiency": self._evaluation("topics/topic-001/items/item-001"),
            "novelty": self._evaluation("past_articles/difference_candidates/difference-001"),
            "reader_value": self._evaluation("summary_ja"),
            "author_specific_question": self._evaluation("screened_request"),
            "uncertainty_impact": {
                **self._evaluation("uncertainties/0"),
                "impact": "MEDIUM",
            },
        }
        evaluations.update(evaluation_updates)
        judgment = {
            "rubric_version": "candidate-v1",
            "judge_id": "judge-test",
            "evaluations": evaluations,
        }
        self.judgment_path.write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _evaluation(packet_ref: str, verdict: str = "PASS", confidence: float = 0.9) -> dict:
        return {
            "verdict": verdict,
            "confidence": confidence,
            "reason_ja": "Packet内の根拠から条件を満たすと判断しました。",
            "packet_refs": [packet_ref],
        }

    def test_accepts_candidate_when_all_required_axes_pass(self) -> None:
        result = judge_candidate(self.judge_input, self.output_dir)
        saved = json.loads(result.decision_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("CANDIDATE_ACCEPTED", "ADVANCE"))
        self.assertEqual(saved["required_human_action"], "none")
        self.assertEqual(saved["rubric_version"], "candidate-v1")

    def test_required_failure_is_normal_no_candidate(self) -> None:
        self._write_judgment(
            novelty=self._evaluation(
                "past_articles/difference_candidates/difference-001", verdict="FAIL"
            )
        )

        result = judge_candidate(self.judge_input, self.output_dir)

        self.assertEqual((result.state_after, result.result), ("NO_CANDIDATE", "NO_CANDIDATE"))

    def test_uncertain_required_axis_holds_without_human_action(self) -> None:
        self._write_judgment(reader_value=self._evaluation("summary_ja", verdict="UNCERTAIN"))

        result = judge_candidate(self.judge_input, self.output_dir)
        saved = json.loads(result.decision_path.read_text(encoding="utf-8"))

        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))
        self.assertEqual(saved["required_human_action"], "none")

    def test_high_impact_uncertainty_holds(self) -> None:
        uncertainty = self._evaluation("uncertainties/0")
        uncertainty["impact"] = "HIGH"
        self._write_judgment(uncertainty_impact=uncertainty)

        result = judge_candidate(self.judge_input, self.output_dir)

        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))

    def test_low_confidence_pass_is_normalized_to_uncertain(self) -> None:
        self._write_judgment(reader_value=self._evaluation("summary_ja", confidence=0.69))

        result = judge_candidate(self.judge_input, self.output_dir)
        saved = json.loads(result.decision_path.read_text(encoding="utf-8"))

        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["evaluations"]["reader_value"]["verdict"], "UNCERTAIN")
        self.assertEqual(
            saved["evaluations"]["reader_value"]["submitted_verdict"], "PASS"
        )

    def test_novelty_cannot_pass_without_past_article(self) -> None:
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        packet["past_articles"] = {
            "status": "UNCONFIRMED_NO_PAST_ARTICLE",
            "known_items": [],
            "difference_candidates": [],
            "recheck_items": [],
        }
        self.packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
        self._write_judgment(novelty=self._evaluation("past_articles"))

        result = judge_candidate(self.judge_input, self.output_dir)

        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))

    def test_rejects_unknown_packet_reference(self) -> None:
        self._write_judgment(reader_value=self._evaluation("topics/missing"))

        with self.assertRaisesRegex(ValueError, "存在しないPacket項目"):
            judge_candidate(self.judge_input, self.output_dir)

    def test_rejects_blank_reason(self) -> None:
        value = self._evaluation("summary_ja")
        value["reason_ja"] = " "
        self._write_judgment(reader_value=value)

        with self.assertRaisesRegex(ValueError, "空でない文字列"):
            judge_candidate(self.judge_input, self.output_dir)

    def test_rejects_missing_axis(self) -> None:
        judgment = json.loads(self.judgment_path.read_text(encoding="utf-8"))
        del judgment["evaluations"]["reader_value"]
        self.judgment_path.write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "5評価軸"):
            judge_candidate(self.judge_input, self.output_dir)

    def test_rejects_non_advanced_packet(self) -> None:
        self._write_packet(result="HOLD")

        with self.assertRaisesRegex(ValueError, "PACKET_READY / ADVANCE"):
            judge_candidate(self.judge_input, self.output_dir)

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = judge_candidate(self.judge_input, self.output_dir)
        first_mtime = first.decision_path.stat().st_mtime_ns

        second = judge_candidate(self.judge_input, self.output_dir)

        self.assertFalse(second.changed)
        self.assertEqual(second.decision_path.stat().st_mtime_ns, first_mtime)


if __name__ == "__main__":
    unittest.main()
