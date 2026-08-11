import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from note.knowledge_harness.validate_draft import ValidationInput, validate_draft


class ValidateDraftTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.draft_path = self.root / "draft.rst"
        self.manifest_path = self.root / "manifest.json"
        self.plan_path = self.root / "plan.json"
        self.packet_path = self.root / "packet.json"
        self.judgment_path = self.root / "judgment.json"
        self.output_dir = self.root / "validations"
        self.posts_dir = self.root / "posts"
        self.repo_root = self.root / "repo"
        self.repo_root.mkdir()
        self.value = ValidationInput(self.draft_path, self.manifest_path, self.plan_path, self.packet_path, self.judgment_path, "2026-08-11T23:00:00Z")
        self._write_inputs()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _draft(self) -> str:
        return """変更を安全に運用する方法
============================

:記事状態: Draft
:公開日: 未確定
:情報基準日: 2026-08-11T18:00:00Z
:対象バージョン: 2.0
:生成動機: 根拠を安全に伝えるため。
:AI担当範囲: 根拠に基づくDraft生成。
:人間の確認範囲: 最終公開判断。

変更点を確認する
----------------

公式情報で確認できる変更点です。

対象外の版は未確認です。
"""

    def _write_inputs(self) -> None:
        draft = self._draft()
        self.draft_path.write_text(draft, encoding="utf-8")
        blocks = [
            {"block_id": "block-001", "body_rst": "公式情報で確認できる変更点です。", "packet_refs": ["topics/topic-001/items/item-001"]},
            {"block_id": "block-002", "body_rst": "対象外の版は未確認です。", "packet_refs": ["uncertainties/0"]},
        ]
        for block in blocks:
            block["sha256"] = hashlib.sha256(block["body_rst"].encode()).hexdigest()
        manifest = {"operation_id": "O-08", "run_id": "run-validation", "state_after": "DRAFT_READY", "result": "ADVANCE", "draft_sha256": hashlib.sha256(draft.encode()).hexdigest(), "sections": [{"section_id": "section-001", "blocks": blocks}]}
        plan = {"operation_id": "O-07", "run_id": "run-validation", "state_after": "PLAN_READY", "result": "ADVANCE", "sections": [{"section_id": "section-001"}]}
        packet = {"operation_id": "O-05", "run_id": "run-validation", "state_after": "PACKET_READY", "result": "ADVANCE", "source_catalog": [{"url": "https://official.example/spec", "final_url": "https://official.example/spec"}]}
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        self.plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        self.packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
        self._write_judgment()

    def _write_judgment(self, verdict: str = "PASS", confidence: float = 0.9, **updates: object) -> None:
        evaluation = {"verdict": verdict, "confidence": confidence, "reason_ja": "根拠と本文を確認しました。", "block_ids": ["block-001"], "packet_refs": ["topics/topic-001/items/item-001"]}
        judgment = {"rubric_version": "draft-validation-v1", "judge_id": "judge-test", "evaluations": {axis: dict(evaluation) for axis in ("factual_grounding", "semantic_leap", "reader_value", "plan_alignment", "uncertainty_handling")}, "policy_change_candidate": {"required": False}}
        judgment.update(updates)
        self.judgment_path.write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")

    def _run(self):
        return validate_draft(self.value, self.output_dir, posts_dir=self.posts_dir, repo_root=self.repo_root)

    def test_validates_clean_draft(self) -> None:
        result = self._run()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        self.assertEqual((result.state_after, result.result), ("VALIDATED", "ADVANCE"))
        self.assertTrue(report["program_validation"]["passed"])
        self.assertEqual(report["required_human_action"], "none")
        self.assertEqual(report["human_guidance_ja"]["status_label_ja"], "検証合格")
        self.assertEqual(report["human_guidance_ja"]["result_label_ja"], "次の工程へ進めます")
        self.assertFalse(report["human_guidance_ja"]["human_action_required"])
        self.assertIn("まだ公開はされません", report["human_guidance_ja"]["summary_ja"])

    def test_low_confidence_pass_holds(self) -> None:
        self._write_judgment(confidence=0.69)
        result = self._run()
        self.assertEqual((result.state_after, result.result), ("HOLD", "HOLD"))

    def test_ai_fail_holds(self) -> None:
        self._write_judgment(verdict="FAIL")
        result = self._run()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(report["human_guidance_ja"]["status_label_ja"], "検証不合格")
        self.assertFalse(report["human_guidance_ja"]["human_action_required"])
        self.assertIn("公開されず保留", report["human_guidance_ja"]["if_no_response_ja"])

    def test_manifest_sha_mismatch_holds(self) -> None:
        self.draft_path.write_text(self._draft() + "改変です。\n", encoding="utf-8")
        result = self._run()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        self.assertEqual(result.result, "HOLD")
        self.assertIn("DRAFT_SHA_MISMATCH", {item["code"] for item in report["program_validation"]["findings"]})

    def test_mechanical_fix_is_saved_without_changing_input(self) -> None:
        draft = self._draft().rstrip("\n")
        self.draft_path.write_text(draft, encoding="utf-8")
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["draft_sha256"] = hashlib.sha256(draft.encode()).hexdigest()
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self._run()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        self.assertIn("FINAL_NEWLINE_ADDED", report["program_validation"]["auto_fixes"])
        self.assertTrue(result.validated_draft_path.read_text(encoding="utf-8").endswith("\n"))
        self.assertFalse(self.draft_path.read_text(encoding="utf-8").endswith("\n"))

    def test_unplanned_external_url_holds(self) -> None:
        draft = self._draft().replace("公式情報で確認できる変更点です。", "https://unknown.example の説明です。")
        self.draft_path.write_text(draft, encoding="utf-8")
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["draft_sha256"] = hashlib.sha256(draft.encode()).hexdigest()
        manifest["sections"][0]["blocks"][0]["body_rst"] = "https://unknown.example の説明です。"
        manifest["sections"][0]["blocks"][0]["sha256"] = hashlib.sha256("https://unknown.example の説明です。".encode()).hexdigest()
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(self._run().result, "HOLD")

    def test_secret_and_personal_information_hold(self) -> None:
        for value in ("api_key=1234567890abcdef", "user@example.com", "03-1234-5678", "社外秘"):
            with self.subTest(value=value):
                self._write_inputs()
                draft = self._draft() + value + "\n"
                self.draft_path.write_text(draft, encoding="utf-8")
                manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                manifest["draft_sha256"] = hashlib.sha256(draft.encode()).hexdigest()
                self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(self._run().result, "HOLD")

    def test_duplicate_title_holds(self) -> None:
        self.posts_dir.mkdir()
        (self.posts_dir / "existing.rst").write_text("変更を安全に運用する方法\n============================\n", encoding="utf-8")
        self.assertEqual(self._run().result, "HOLD")

    def test_similarity_candidate_is_warning_not_program_error(self) -> None:
        self.posts_dir.mkdir()
        (self.posts_dir / "existing.rst").write_text(self._draft().replace("変更を安全に運用する方法", "別の題名です"), encoding="utf-8")
        result = self._run()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        self.assertEqual(result.result, "ADVANCE")
        self.assertIn("DUPLICATE_BODY_CANDIDATE", {item["code"] for item in report["program_validation"]["findings"]})

    def test_policy_candidate_holds_for_human_policy_action(self) -> None:
        judgment = json.loads(self.judgment_path.read_text(encoding="utf-8"))
        judgment["policy_change_candidate"] = {"required": True, "title_ja": "恒久方針が必要です", "problem_ja": "現行方針では判定できません。", "options": [{"option_ja": "現状維持", "impact_ja": "公開を保留します。"}, {"option_ja": "方針追加", "impact_ja": "今後の検査が変わります。"}]}
        self.judgment_path.write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")
        result = self._run()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(report["human_guidance_ja"]["status_label_ja"], "方針判断待ち")
        self.assertTrue(report["human_guidance_ja"]["human_action_required"])
        self.assertIn("採用する方針", report["human_guidance_ja"]["requested_decision_ja"])
        self.assertEqual(report["required_human_action"], "policy")

    def test_rejects_unknown_ai_references(self) -> None:
        judgment = json.loads(self.judgment_path.read_text(encoding="utf-8"))
        judgment["evaluations"]["reader_value"]["block_ids"] = ["missing"]
        self.judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "存在しないDraftブロック"):
            self._run()

    def test_rejects_mismatched_run_id(self) -> None:
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        packet["run_id"] = "another-run"
        self.packet_path.write_text(json.dumps(packet), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "run_idが一致"):
            self._run()

    def test_identical_rerun_does_not_rewrite(self) -> None:
        first = self._run()
        report_mtime = first.report_path.stat().st_mtime_ns
        draft_mtime = first.validated_draft_path.stat().st_mtime_ns
        second = self._run()
        self.assertFalse(second.changed)
        self.assertEqual(second.report_path.stat().st_mtime_ns, report_mtime)
        self.assertEqual(second.validated_draft_path.stat().st_mtime_ns, draft_mtime)


if __name__ == "__main__":
    unittest.main()
