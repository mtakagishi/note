import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from note.knowledge_harness.collect_evidence import CollectionLimits, FetchResult
from note.knowledge_harness.orchestrate_run import (
    OrchestrationInput,
    OrchestrationResult,
    orchestrate_run,
)


class OrchestrateRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temporary_directory.name) / "runs"
        self.orchestration_input = OrchestrationInput(
            run_id="run-20260811-003",
            question_ja="公開 Issue から記事候補を安全に取り込むには？",
            source_ref="issue:9",
            source_kind="public_issue",
            labels=["knowledge-harness:run"],
            required_label="knowledge-harness:run",
            assessment="auto",
            restricted_terms=[],
            created_at="2026-08-11T09:00:00Z",
            sources_path=None,
            packet_draft_path=None,
            evidence_limits=CollectionLimits(search_rounds=1, queries_per_round=1, retrievals=1, adopted_sources=1, per_domain=1, max_seconds=60, retries=0),
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_complete_flow_advances_through_all_operations(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        draft_path = self.output_dir / "draft.json"
        draft_path.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "topic-1",
                            "title_ja": "要点",
                            "items": [
                                {
                                    "item_id": "item-1",
                                    "kind": "fact",
                                    "statement_ja": "要点を整理した",
                                    "source_ids": ["source-001"],
                                }
                            ],
                        }
                    ],
                    "past_articles": {
                        "article_refs": ["article-001"],
                        "difference_candidates": [
                            {
                                "item_id": "difference-001",
                                "kind": "fact",
                                "statement_ja": "差分候補",
                                "source_ids": ["source-001"],
                            }
                        ],
                    },
                    "summary_ja": "要点の整理案",
                }
            ),
            encoding="utf-8",
        )
        judgment_path = self.output_dir / "judgment.json"
        judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "candidate-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "evidence_sufficiency": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "十分な証拠があります。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "novelty": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "新規性があります。",
                            "packet_refs": ["past_articles/difference_candidates/difference-001"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "読者価値があります。",
                            "packet_refs": ["summary_ja"],
                        },
                        "author_specific_question": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "著者の問いに答えています。",
                            "packet_refs": ["screened_request"],
                        },
                        "uncertainty_impact": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "不確実性は小さく、産業価値があります。",
                            "packet_refs": ["summary_ja"],
                            "impact": "LOW",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        plan_draft_path = self.output_dir / "plan-draft.json"
        plan_draft_path.write_text(
            json.dumps(
                {
                    "mode": "PLAN",
                    "plan_version": "article-plan-v1",
                    "planner_id": "planner-test",
                    "working_title_ja": "run-20260811-003 の安全運用メモ",
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
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        }
                    ],
                    "excluded_topics": [
                        {
                            "topic_ja": "対象外の版",
                            "reason_ja": "根拠を確認できないためです。",
                        }
                    ],
                    "uncertainty_treatments": [],
                }
            ),
            encoding="utf-8",
        )
        proposal_path = self.output_dir / "proposal.json"
        proposal_path.write_text(
            json.dumps(
                {
                    "draft_version": "article-draft-v1",
                    "drafter_id": "drafter-test",
                    "sections": [
                        {
                            "section_id": "section-001",
                            "blocks": [
                                {
                                    "block_id": "block-001",
                                    "body_rst": "公式情報で確認できる変更点を説明します。",
                                    "packet_refs": ["topics/topic-1/items/item-1"],
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        validation_judgment_path = self.output_dir / "validation-judgment.json"
        validation_judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "draft-validation-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "factual_grounding": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "semantic_leap": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "plan_alignment": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "uncertainty_handling": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                    },
                    "policy_change_candidate": {"required": False},
                }
            ),
            encoding="utf-8",
        )
        review_proposal_path = self.output_dir / "review-proposal.json"
        review_proposal_path.write_text(
            json.dumps(
                {
                    "review_version": "review-v1",
                    "preparer_id": "preparer-test",
                    "final_title_ja": "変更を安全に確認する方法",
                    "slug": "safe-change-review",
                    "tags": ["運用", "検証"],
                    "category_ja": "運用改善",
                    "author": "mtakagishi",
                }
            ),
            encoding="utf-8",
        )
        publication_snapshot_path = self.output_dir / "pr-snapshot.json"
        publication_snapshot_path.write_text(
            json.dumps(
                {
                    "repository": "mtakagishi/note",
                    "number": 99,
                    "base": "main",
                    "head": f"article/{self.orchestration_input.run_id}",
                    "head_sha": "abc123",
                    "url": "https://github.com/mtakagishi/note/pull/99",
                    "merged": True,
                    "merged_by": "mtakagishi",
                    "merge_commit_sha": "merge123",
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=draft_path,
            judgment_path=judgment_path,
            plan_draft_path=plan_draft_path,
            proposal_path=proposal_path,
            validation_judgment_path=validation_judgment_path,
            review_proposal_path=review_proposal_path,
            publication_pr_snapshot_path=publication_snapshot_path,
            publication_repository="mtakagishi/note",
            publication_pr_number=99,
            publication_authorized_actors=("mtakagishi",),
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertTrue(result.changed)
        self.assertEqual(result.state_after, "APPROVED")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06", "O-07", "O-08", "O-09", "O-10", "O-11", "O-13"])
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "request.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "authorization.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "screening.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "evidence.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "evidence_packet.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "candidate_decision.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "article_plan.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "draft.rst").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "draft_manifest.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "validated_draft.rst").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "validation_report.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "review_packet.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "publication_decision.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "outcome.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "HANDOFF.md").exists())
        self.assertTrue((self.output_dir / "metrics.json").exists())
        self.assertTrue((self.output_dir / "review_posts" / "2026-08-12-safe-change-review.rst").exists())

    def test_revision_decision_advances_to_apply_feedback(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        draft_path = self.output_dir / "draft.json"
        draft_path.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "topic-1",
                            "title_ja": "要点",
                            "items": [
                                {
                                    "item_id": "item-1",
                                    "kind": "fact",
                                    "statement_ja": "要点を整理した",
                                    "source_ids": ["source-001"],
                                }
                            ],
                        }
                    ],
                    "past_articles": {
                        "article_refs": ["article-001"],
                        "difference_candidates": [
                            {
                                "item_id": "difference-001",
                                "kind": "fact",
                                "statement_ja": "差分候補",
                                "source_ids": ["source-001"],
                            }
                        ],
                    },
                    "summary_ja": "要点の整理案",
                }
            ),
            encoding="utf-8",
        )
        judgment_path = self.output_dir / "judgment.json"
        judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "candidate-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "evidence_sufficiency": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "十分な証拠があります。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "novelty": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "新規性があります。",
                            "packet_refs": ["past_articles/difference_candidates/difference-001"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "読者価値があります。",
                            "packet_refs": ["summary_ja"],
                        },
                        "author_specific_question": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "著者の問いに答えています。",
                            "packet_refs": ["screened_request"],
                        },
                        "uncertainty_impact": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "不確実性は小さく、産業価値があります。",
                            "packet_refs": ["summary_ja"],
                            "impact": "LOW",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        plan_draft_path = self.output_dir / "plan-draft.json"
        plan_draft_path.write_text(
            json.dumps(
                {
                    "mode": "PLAN",
                    "plan_version": "article-plan-v1",
                    "planner_id": "planner-test",
                    "working_title_ja": "run-20260811-003 の安全運用メモ",
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
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        }
                    ],
                    "excluded_topics": [
                        {
                            "topic_ja": "対象外の版",
                            "reason_ja": "根拠を確認できないためです。",
                        }
                    ],
                    "uncertainty_treatments": [],
                }
            ),
            encoding="utf-8",
        )
        proposal_path = self.output_dir / "proposal.json"
        proposal_path.write_text(
            json.dumps(
                {
                    "draft_version": "article-draft-v1",
                    "drafter_id": "drafter-test",
                    "sections": [
                        {
                            "section_id": "section-001",
                            "blocks": [
                                {
                                    "block_id": "block-001",
                                    "body_rst": "公式情報で確認できる変更点を説明します。",
                                    "packet_refs": ["topics/topic-1/items/item-1"],
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        validation_judgment_path = self.output_dir / "validation-judgment.json"
        validation_judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "draft-validation-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "factual_grounding": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "semantic_leap": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "plan_alignment": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "uncertainty_handling": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                    },
                    "policy_change_candidate": {"required": False},
                }
            ),
            encoding="utf-8",
        )
        review_proposal_path = self.output_dir / "review-proposal.json"
        review_proposal_path.write_text(
            json.dumps(
                {
                    "review_version": "review-v1",
                    "preparer_id": "preparer-test",
                    "final_title_ja": "変更を安全に確認する方法",
                    "slug": "safe-change-review",
                    "tags": ["運用", "検証"],
                    "category_ja": "運用改善",
                    "author": "mtakagishi",
                }
            ),
            encoding="utf-8",
        )
        publication_snapshot_path = self.output_dir / "pr-snapshot.json"
        publication_snapshot_path.write_text(
            json.dumps(
                {
                    "repository": "mtakagishi/note",
                    "number": 99,
                    "base": "main",
                    "head": f"article/{self.orchestration_input.run_id}",
                    "head_sha": "abc123",
                    "url": "https://github.com/mtakagishi/note/pull/99",
                    "merged": False,
                    "merged_by": None,
                    "merge_commit_sha": None,
                }
            ),
            encoding="utf-8",
        )
        publication_human_decision_path = self.output_dir / "human-decision.json"
        publication_human_decision_path.write_text(
            json.dumps(
                {
                    "decisions": [
                        {
                            "decision": "revision",
                            "actor": "mtakagishi",
                            "decided_at": "2026-08-11T10:00:00Z",
                            "reason_ja": "冒頭の表現を調整したい。",
                            "instruction_ja": "冒頭を簡潔にしてください。",
                            "target_ja": "冒頭段落",
                            "source": {
                                "url": "https://github.com/mtakagishi/note/pull/99#issuecomment-1",
                                "reference_id": "comment-1",
                                "target_commit_sha": "abc123",
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        feedback_proposal_path = self.output_dir / "feedback-proposal.json"
        feedback_proposal_path.write_text(
            json.dumps(
                {
                    "instruction_ja": "冒頭を簡潔にしてください。",
                    "target_ja": "冒頭段落",
                    "changes": [
                        {
                            "block_id": "block-001",
                            "body_rst": "簡潔な冒頭です。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=draft_path,
            judgment_path=judgment_path,
            plan_draft_path=plan_draft_path,
            proposal_path=proposal_path,
            validation_judgment_path=validation_judgment_path,
            review_proposal_path=review_proposal_path,
            publication_pr_snapshot_path=publication_snapshot_path,
            publication_human_decision_path=publication_human_decision_path,
            publication_repository="mtakagishi/note",
            publication_pr_number=99,
            publication_authorized_actors=("mtakagishi",),
            feedback_proposal_path=feedback_proposal_path,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "VALIDATED")
        self.assertEqual(result.result, "ADVANCE")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06", "O-07", "O-08", "O-09", "O-10", "O-11", "O-12", "O-09"])
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "publication_decision.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "revised_draft.rst").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "revision_manifest.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "validated_draft.rst").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "validation_report.json").exists())

    def test_missing_feedback_proposal_stops_before_apply_feedback(self) -> None:
        import note.knowledge_harness.orchestrate_run as orchestrator_module

        stub_input = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=self.output_dir / "sources.json",
            packet_draft_path=self.output_dir / "draft.json",
            judgment_path=self.output_dir / "judgment.json",
            plan_draft_path=self.output_dir / "plan-draft.json",
            proposal_path=self.output_dir / "proposal.json",
            validation_judgment_path=self.output_dir / "validation-judgment.json",
            review_proposal_path=self.output_dir / "review-proposal.json",
            publication_pr_snapshot_path=self.output_dir / "pr-snapshot.json",
            publication_repository="mtakagishi/note",
            publication_pr_number=99,
            publication_authorized_actors=("mtakagishi",),
            feedback_proposal_path=None,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        run_dir = self.output_dir / self.orchestration_input.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "review_packet.json").write_text(
            json.dumps({"publication_candidate": {"path": str(run_dir / "article.rst")}}),
            encoding="utf-8",
        )

        original_collect = orchestrator_module.collect_evidence
        original_packet = orchestrator_module.build_evidence_packet
        original_judge = orchestrator_module.judge_candidate
        original_plan = orchestrator_module.plan_article
        original_draft = orchestrator_module.draft_article
        original_validate = orchestrator_module.validate_draft
        original_review = orchestrator_module.prepare_review
        original_publication = orchestrator_module.decide_publication

        try:
            orchestrator_module.collect_evidence = lambda *_args, **_kwargs: SimpleNamespace(state_after="EVIDENCE_READY", result="ADVANCE")
            orchestrator_module.build_evidence_packet = lambda *_args, **_kwargs: SimpleNamespace(state_after="PACKET_READY", result="ADVANCE")
            orchestrator_module.judge_candidate = lambda *_args, **_kwargs: SimpleNamespace(state_after="CANDIDATE_ACCEPTED", result="ADVANCE")
            orchestrator_module.plan_article = lambda *_args, **_kwargs: SimpleNamespace(state_after="PLAN_READY", result="ADVANCE")
            orchestrator_module.draft_article = lambda *_args, **_kwargs: SimpleNamespace(state_after="DRAFT_READY", result="ADVANCE")
            orchestrator_module.validate_draft = lambda *_args, **_kwargs: SimpleNamespace(state_after="VALIDATED", result="ADVANCE")
            orchestrator_module.prepare_review = lambda *_args, **_kwargs: SimpleNamespace(state_after="REVIEW_READY", result="ADVANCE")
            orchestrator_module.decide_publication = lambda *_args, **_kwargs: SimpleNamespace(state_after="REVISION", result="ADVANCE")

            result = orchestrate_run(stub_input, self.output_dir)
        finally:
            orchestrator_module.collect_evidence = original_collect
            orchestrator_module.build_evidence_packet = original_packet
            orchestrator_module.judge_candidate = original_judge
            orchestrator_module.plan_article = original_plan
            orchestrator_module.draft_article = original_draft
            orchestrator_module.validate_draft = original_validate
            orchestrator_module.prepare_review = original_review
            orchestrator_module.decide_publication = original_publication

        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(result.state_after, "REVISION")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06", "O-07", "O-08", "O-09", "O-10", "O-11"])
        self.assertEqual(saved["stop_reason"], "FEEDBACK_PROPOSAL_MISSING")
        self.assertEqual(saved["resume_position"], "O-12")
        self.assertEqual(saved["next_action"], "O-12 Apply Feedbackの入力を補完して再開する")

    def test_apply_feedback_prefers_latest_revised_artifacts(self) -> None:
        import note.knowledge_harness.orchestrate_run as orchestrator_module

        run_dir = self.output_dir / self.orchestration_input.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "draft.rst").write_text("original draft\n", encoding="utf-8")
        (run_dir / "draft_manifest.json").write_text("{}", encoding="utf-8")
        (run_dir / "revised_draft.rst").write_text("revised draft\n", encoding="utf-8")
        (run_dir / "revision_manifest.json").write_text("{}", encoding="utf-8")
        (run_dir / "review_packet.json").write_text(
            json.dumps({"publication_candidate": {"path": str(run_dir / "article.rst")}}),
            encoding="utf-8",
        )

        stub_input = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=self.output_dir / "sources.json",
            packet_draft_path=self.output_dir / "draft.json",
            judgment_path=self.output_dir / "judgment.json",
            plan_draft_path=self.output_dir / "plan-draft.json",
            proposal_path=self.output_dir / "proposal.json",
            validation_judgment_path=self.output_dir / "validation-judgment.json",
            review_proposal_path=self.output_dir / "review-proposal.json",
            publication_pr_snapshot_path=self.output_dir / "pr-snapshot.json",
            publication_repository="mtakagishi/note",
            publication_pr_number=99,
            publication_authorized_actors=("mtakagishi",),
            feedback_proposal_path=self.output_dir / "feedback-proposal.json",
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        captured: dict[str, Path] = {}

        def stub_apply_feedback(value, _output_dir):
            captured["draft_path"] = value.draft_path
            captured["manifest_path"] = value.manifest_path
            return SimpleNamespace(state_after="HOLD", result="HOLD")

        original_collect = orchestrator_module.collect_evidence
        original_packet = orchestrator_module.build_evidence_packet
        original_judge = orchestrator_module.judge_candidate
        original_plan = orchestrator_module.plan_article
        original_draft = orchestrator_module.draft_article
        original_validate = orchestrator_module.validate_draft
        original_review = orchestrator_module.prepare_review
        original_publication = orchestrator_module.decide_publication
        original_apply_feedback = orchestrator_module.apply_feedback

        try:
            orchestrator_module.collect_evidence = lambda *_args, **_kwargs: SimpleNamespace(state_after="EVIDENCE_READY", result="ADVANCE")
            orchestrator_module.build_evidence_packet = lambda *_args, **_kwargs: SimpleNamespace(state_after="PACKET_READY", result="ADVANCE")
            orchestrator_module.judge_candidate = lambda *_args, **_kwargs: SimpleNamespace(state_after="CANDIDATE_ACCEPTED", result="ADVANCE")
            orchestrator_module.plan_article = lambda *_args, **_kwargs: SimpleNamespace(state_after="PLAN_READY", result="ADVANCE")
            orchestrator_module.draft_article = lambda *_args, **_kwargs: SimpleNamespace(state_after="DRAFT_READY", result="ADVANCE")
            orchestrator_module.validate_draft = lambda *_args, **_kwargs: SimpleNamespace(state_after="VALIDATED", result="ADVANCE")
            orchestrator_module.prepare_review = lambda *_args, **_kwargs: SimpleNamespace(state_after="REVIEW_READY", result="ADVANCE")
            orchestrator_module.decide_publication = lambda *_args, **_kwargs: SimpleNamespace(state_after="REVISION", result="ADVANCE")
            orchestrator_module.apply_feedback = stub_apply_feedback

            result = orchestrate_run(stub_input, self.output_dir)
        finally:
            orchestrator_module.collect_evidence = original_collect
            orchestrator_module.build_evidence_packet = original_packet
            orchestrator_module.judge_candidate = original_judge
            orchestrator_module.plan_article = original_plan
            orchestrator_module.draft_article = original_draft
            orchestrator_module.validate_draft = original_validate
            orchestrator_module.prepare_review = original_review
            orchestrator_module.decide_publication = original_publication
            orchestrator_module.apply_feedback = original_apply_feedback

        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(captured["draft_path"], run_dir / "revised_draft.rst")
        self.assertEqual(captured["manifest_path"], run_dir / "revision_manifest.json")
        self.assertEqual(result.state_after, "REVISION")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["stop_reason"], "APPLY_FEEDBACK_HOLD")
        self.assertEqual(saved["resume_position"], "O-12")
        self.assertEqual(saved["next_action"], "O-12 Apply Feedbackを再実行して再開する")

    def test_publication_input_missing_sets_action_to_complete_inputs(self) -> None:
        import note.knowledge_harness.orchestrate_run as orchestrator_module

        stub_input = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=self.output_dir / "sources.json",
            packet_draft_path=self.output_dir / "draft.json",
            judgment_path=self.output_dir / "judgment.json",
            plan_draft_path=self.output_dir / "plan-draft.json",
            proposal_path=self.output_dir / "proposal.json",
            validation_judgment_path=self.output_dir / "validation-judgment.json",
            review_proposal_path=self.output_dir / "review-proposal.json",
            publication_pr_snapshot_path=None,
            publication_repository=None,
            publication_pr_number=None,
            publication_authorized_actors=(),
            feedback_proposal_path=self.output_dir / "feedback-proposal.json",
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        original_collect = orchestrator_module.collect_evidence
        original_packet = orchestrator_module.build_evidence_packet
        original_judge = orchestrator_module.judge_candidate
        original_plan = orchestrator_module.plan_article
        original_draft = orchestrator_module.draft_article
        original_validate = orchestrator_module.validate_draft
        original_review = orchestrator_module.prepare_review

        try:
            orchestrator_module.collect_evidence = lambda *_args, **_kwargs: SimpleNamespace(state_after="EVIDENCE_READY", result="ADVANCE")
            orchestrator_module.build_evidence_packet = lambda *_args, **_kwargs: SimpleNamespace(state_after="PACKET_READY", result="ADVANCE")
            orchestrator_module.judge_candidate = lambda *_args, **_kwargs: SimpleNamespace(state_after="CANDIDATE_ACCEPTED", result="ADVANCE")
            orchestrator_module.plan_article = lambda *_args, **_kwargs: SimpleNamespace(state_after="PLAN_READY", result="ADVANCE")
            orchestrator_module.draft_article = lambda *_args, **_kwargs: SimpleNamespace(state_after="DRAFT_READY", result="ADVANCE")
            orchestrator_module.validate_draft = lambda *_args, **_kwargs: SimpleNamespace(state_after="VALIDATED", result="ADVANCE")
            orchestrator_module.prepare_review = lambda *_args, **_kwargs: SimpleNamespace(state_after="REVIEW_READY", result="ADVANCE")

            result = orchestrate_run(stub_input, self.output_dir)
        finally:
            orchestrator_module.collect_evidence = original_collect
            orchestrator_module.build_evidence_packet = original_packet
            orchestrator_module.judge_candidate = original_judge
            orchestrator_module.plan_article = original_plan
            orchestrator_module.draft_article = original_draft
            orchestrator_module.validate_draft = original_validate
            orchestrator_module.prepare_review = original_review

        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual(result.state_after, "REVIEW_READY")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["stop_reason"], "PUBLICATION_DECISION_INPUT_MISSING")
        self.assertEqual(saved["resume_position"], "O-11")
        self.assertEqual(saved["next_action"], "O-11 Decide Publicationの入力を補完して再開する")

    def test_advances_to_candidate_decision_when_judgment_is_provided(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        draft_path = self.output_dir / "draft.json"
        draft_path.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "topic-1",
                            "title_ja": "要点",
                            "items": [
                                {
                                    "item_id": "item-1",
                                    "kind": "fact",
                                    "statement_ja": "要点を整理した",
                                    "source_ids": ["source-001"],
                                }
                            ],
                        }
                    ],
                    "past_articles": {
                        "article_refs": ["article-001"],
                        "difference_candidates": [
                            {
                                "item_id": "difference-001",
                                "kind": "fact",
                                "statement_ja": "差分候補",
                                "source_ids": ["source-001"],
                            }
                        ],
                    },
                    "summary_ja": "要点の整理案",
                }
            ),
            encoding="utf-8",
        )
        judgment_path = self.output_dir / "judgment.json"
        judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "candidate-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "evidence_sufficiency": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "十分な証拠があります。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "novelty": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "新規性があります。",
                            "packet_refs": ["past_articles/difference_candidates/difference-001"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "読者価値があります。",
                            "packet_refs": ["summary_ja"],
                        },
                        "author_specific_question": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "著者の問いに答えています。",
                            "packet_refs": ["screened_request"],
                        },
                        "uncertainty_impact": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "不確実性は小さく、産業価値があります。",
                            "packet_refs": ["summary_ja"],
                            "impact": "LOW",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=draft_path,
            judgment_path=judgment_path,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "CANDIDATE_ACCEPTED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06"])
        self.assertEqual(saved["stop_reason"], "PLAN_DRAFT_MISSING")
        self.assertEqual(saved["resume_position"], "O-07")
        self.assertEqual(saved["next_action"], "O-07 Plan Articleの入力を補完して再開する")
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "candidate_decision.json").exists())

    def test_missing_validation_judgment_stops_before_validate_draft(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        draft_path = self.output_dir / "draft.json"
        draft_path.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "topic-1",
                            "title_ja": "要点",
                            "items": [
                                {
                                    "item_id": "item-1",
                                    "kind": "fact",
                                    "statement_ja": "要点を整理した",
                                    "source_ids": ["source-001"],
                                }
                            ],
                        }
                    ],
                    "past_articles": {
                        "article_refs": ["article-001"],
                        "difference_candidates": [
                            {
                                "item_id": "difference-001",
                                "kind": "fact",
                                "statement_ja": "差分候補",
                                "source_ids": ["source-001"],
                            }
                        ],
                    },
                    "summary_ja": "要点の整理案",
                }
            ),
            encoding="utf-8",
        )
        judgment_path = self.output_dir / "judgment.json"
        judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "candidate-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "evidence_sufficiency": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "十分な証拠があります。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "novelty": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "新規性があります。",
                            "packet_refs": ["past_articles/difference_candidates/difference-001"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "読者価値があります。",
                            "packet_refs": ["summary_ja"],
                        },
                        "author_specific_question": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "著者の問いに答えています。",
                            "packet_refs": ["screened_request"],
                        },
                        "uncertainty_impact": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "不確実性は小さく、産業価値があります。",
                            "packet_refs": ["summary_ja"],
                            "impact": "LOW",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        plan_draft_path = self.output_dir / "plan-draft.json"
        plan_draft_path.write_text(
            json.dumps(
                {
                    "mode": "PLAN",
                    "plan_version": "article-plan-v1",
                    "planner_id": "planner-test",
                    "working_title_ja": "run-20260811-003 の安全運用メモ",
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
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        }
                    ],
                    "excluded_topics": [
                        {
                            "topic_ja": "対象外の版",
                            "reason_ja": "根拠を確認できないためです。",
                        }
                    ],
                    "uncertainty_treatments": [],
                }
            ),
            encoding="utf-8",
        )
        proposal_path = self.output_dir / "proposal.json"
        proposal_path.write_text(
            json.dumps(
                {
                    "draft_version": "article-draft-v1",
                    "drafter_id": "drafter-test",
                    "sections": [
                        {
                            "section_id": "section-001",
                            "blocks": [
                                {
                                    "block_id": "block-001",
                                    "body_rst": "公式情報で確認できる変更点を説明します。",
                                    "packet_refs": ["topics/topic-1/items/item-1"],
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=draft_path,
            judgment_path=judgment_path,
            plan_draft_path=plan_draft_path,
            proposal_path=proposal_path,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "DRAFT_READY")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06", "O-07", "O-08"])
        self.assertEqual(saved["stop_reason"], "VALIDATION_JUDGMENT_MISSING")
        self.assertEqual(saved["resume_position"], "O-09")
        self.assertEqual(saved["next_action"], "O-09 Validate Draftの入力を補完して再開する")
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "article_plan.json").exists())
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "draft.rst").exists())

    def test_missing_review_proposal_stops_before_prepare_review(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        draft_path = self.output_dir / "draft.json"
        draft_path.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "topic-1",
                            "title_ja": "要点",
                            "items": [
                                {
                                    "item_id": "item-1",
                                    "kind": "fact",
                                    "statement_ja": "要点を整理した",
                                    "source_ids": ["source-001"],
                                }
                            ],
                        }
                    ],
                    "past_articles": {
                        "article_refs": ["article-001"],
                        "difference_candidates": [
                            {
                                "item_id": "difference-001",
                                "kind": "fact",
                                "statement_ja": "差分候補",
                                "source_ids": ["source-001"],
                            }
                        ],
                    },
                    "summary_ja": "要点の整理案",
                }
            ),
            encoding="utf-8",
        )
        judgment_path = self.output_dir / "judgment.json"
        judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "candidate-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "evidence_sufficiency": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "十分な証拠があります。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "novelty": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "新規性があります。",
                            "packet_refs": ["past_articles/difference_candidates/difference-001"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "読者価値があります。",
                            "packet_refs": ["summary_ja"],
                        },
                        "author_specific_question": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "著者の問いに答えています。",
                            "packet_refs": ["screened_request"],
                        },
                        "uncertainty_impact": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "不確実性は小さく、産業価値があります。",
                            "packet_refs": ["summary_ja"],
                            "impact": "LOW",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        plan_draft_path = self.output_dir / "plan-draft.json"
        plan_draft_path.write_text(
            json.dumps(
                {
                    "mode": "PLAN",
                    "plan_version": "article-plan-v1",
                    "planner_id": "planner-test",
                    "working_title_ja": "run-20260811-003 の安全運用メモ",
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
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        }
                    ],
                    "excluded_topics": [
                        {
                            "topic_ja": "対象外の版",
                            "reason_ja": "根拠を確認できないためです。",
                        }
                    ],
                    "uncertainty_treatments": [],
                }
            ),
            encoding="utf-8",
        )
        proposal_path = self.output_dir / "proposal.json"
        proposal_path.write_text(
            json.dumps(
                {
                    "draft_version": "article-draft-v1",
                    "drafter_id": "drafter-test",
                    "sections": [
                        {
                            "section_id": "section-001",
                            "blocks": [
                                {
                                    "block_id": "block-001",
                                    "body_rst": "公式情報で確認できる変更点を説明します。",
                                    "packet_refs": ["topics/topic-1/items/item-1"],
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        validation_judgment_path = self.output_dir / "validation-judgment.json"
        validation_judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "draft-validation-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "factual_grounding": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "semantic_leap": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "plan_alignment": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "uncertainty_handling": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "根拠と本文を確認しました。",
                            "block_ids": ["block-001"],
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                    },
                    "policy_change_candidate": {"required": False},
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=draft_path,
            judgment_path=judgment_path,
            plan_draft_path=plan_draft_path,
            proposal_path=proposal_path,
            validation_judgment_path=validation_judgment_path,
            review_proposal_path=None,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "VALIDATED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06", "O-07", "O-08", "O-09"])
        self.assertEqual(saved["stop_reason"], "REVIEW_PROPOSAL_MISSING")
        self.assertEqual(saved["resume_position"], "O-10")
        self.assertEqual(saved["next_action"], "O-10 Prepare Reviewの入力を補完して再開する")
        self.assertTrue((self.output_dir / self.orchestration_input.run_id / "validation_report.json").exists())

    def test_missing_proposal_stops_before_draft_article(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "url": "https://example.com/spec",
                            "source_type": "primary",
                            "search_round": 1,
                            "query": "example spec",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        draft_path = self.output_dir / "draft.json"
        draft_path.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "topic-1",
                            "title_ja": "要点",
                            "items": [
                                {
                                    "item_id": "item-1",
                                    "kind": "fact",
                                    "statement_ja": "要点を整理した",
                                    "source_ids": ["source-001"],
                                }
                            ],
                        }
                    ],
                    "past_articles": {
                        "article_refs": ["article-001"],
                        "difference_candidates": [
                            {
                                "item_id": "difference-001",
                                "kind": "fact",
                                "statement_ja": "差分候補",
                                "source_ids": ["source-001"],
                            }
                        ],
                    },
                    "summary_ja": "要点の整理案",
                }
            ),
            encoding="utf-8",
        )
        judgment_path = self.output_dir / "judgment.json"
        judgment_path.write_text(
            json.dumps(
                {
                    "rubric_version": "candidate-v1",
                    "judge_id": "judge-test",
                    "evaluations": {
                        "evidence_sufficiency": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "十分な証拠があります。",
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        },
                        "novelty": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "新規性があります。",
                            "packet_refs": ["past_articles/difference_candidates/difference-001"],
                        },
                        "reader_value": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "読者価値があります。",
                            "packet_refs": ["summary_ja"],
                        },
                        "author_specific_question": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "著者の問いに答えています。",
                            "packet_refs": ["screened_request"],
                        },
                        "uncertainty_impact": {
                            "verdict": "PASS",
                            "confidence": 0.9,
                            "reason_ja": "不確実性は小さく、産業価値があります。",
                            "packet_refs": ["summary_ja"],
                            "impact": "LOW",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        plan_draft_path = self.output_dir / "plan-draft.json"
        plan_draft_path.write_text(
            json.dumps(
                {
                    "mode": "PLAN",
                    "plan_version": "article-plan-v1",
                    "planner_id": "planner-test",
                    "working_title_ja": "run-20260811-003 の安全運用メモ",
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
                            "packet_refs": ["topics/topic-1/items/item-1"],
                        }
                    ],
                    "excluded_topics": [
                        {
                            "topic_ja": "対象外の版",
                            "reason_ja": "根拠を確認できないためです。",
                        }
                    ],
                    "uncertainty_treatments": [],
                }
            ),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=draft_path,
            judgment_path=judgment_path,
            plan_draft_path=plan_draft_path,
            proposal_path=None,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "PLAN_READY")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06", "O-07"])
        self.assertEqual(saved["stop_reason"], "DRAFT_PROPOSAL_MISSING")
        self.assertEqual(saved["resume_position"], "O-08")
        self.assertEqual(saved["next_action"], "O-08 Draft Articleの入力を補完して再開する")

    def test_missing_sources_stops_before_evidence_collection(self) -> None:
        result = orchestrate_run(self.orchestration_input, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "SCREENED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03"])
        self.assertEqual(saved["stop_reason"], "EVIDENCE_INPUT_MISSING")
        self.assertEqual(saved["resume_position"], "O-04")
        self.assertEqual(saved["next_action"], "O-04 Collect Evidenceの入力を補完して再開する")

    def test_missing_packet_draft_stops_before_evidence_packet(self) -> None:
        sources_path = self.output_dir / "sources.json"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(
            json.dumps({"sources": [{"url": "https://example.com/spec", "source_type": "primary", "search_round": 1, "query": "example spec"}]}),
            encoding="utf-8",
        )
        input_with_sources = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=sources_path,
            packet_draft_path=None,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        def fetch(url: str) -> FetchResult:
            return FetchResult(url, 200, "text/html", f"body:{url}".encode())

        result = orchestrate_run(input_with_sources, self.output_dir, fetcher=fetch)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "EVIDENCE_READY")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03", "O-04"])
        self.assertEqual(saved["stop_reason"], "PACKET_DRAFT_MISSING")
        self.assertEqual(saved["resume_position"], "O-05")
        self.assertEqual(saved["next_action"], "O-05 Evidence Packetの入力を補完して再開する")

    def test_missing_label_stops_before_screening(self) -> None:
        input_without_label = self.orchestration_input
        input_without_label = input_without_label.__class__(
            run_id=input_without_label.run_id,
            question_ja=input_without_label.question_ja,
            source_ref=input_without_label.source_ref,
            source_kind=input_without_label.source_kind,
            labels=[],
            required_label="knowledge-harness:run",
            assessment=input_without_label.assessment,
            restricted_terms=input_without_label.restricted_terms,
            created_at=input_without_label.created_at,
        )

        result = orchestrate_run(input_without_label, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "CAPTURED")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02"])
        self.assertEqual(saved["stop_reason"], "RUN_LABEL_MISSING")
        self.assertEqual(saved["resume_position"], "O-02")
        self.assertEqual(saved["next_action"], "O-02 Authorize Runの入力を補完して再開する")
        self.assertFalse((self.output_dir / self.orchestration_input.run_id / "screening.json").exists())

    def test_unconfirmed_input_stops_at_capture_request(self) -> None:
        input_unconfirmed = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind="unconfirmed_input",
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment=self.orchestration_input.assessment,
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=self.orchestration_input.sources_path,
            packet_draft_path=self.orchestration_input.packet_draft_path,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        result = orchestrate_run(input_unconfirmed, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "HOLD")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01"])
        self.assertEqual(saved["stop_reason"], "REQUEST_HOLD")
        self.assertEqual(saved["resume_position"], "O-01")
        self.assertEqual(saved["next_action"], "O-01 Capture Requestの入力を補完して再開する")

    def test_uncertain_assessment_stops_at_screening(self) -> None:
        input_uncertain = self.orchestration_input.__class__(
            run_id=self.orchestration_input.run_id,
            question_ja=self.orchestration_input.question_ja,
            source_ref=self.orchestration_input.source_ref,
            source_kind=self.orchestration_input.source_kind,
            labels=self.orchestration_input.labels,
            required_label=self.orchestration_input.required_label,
            assessment="uncertain",
            restricted_terms=self.orchestration_input.restricted_terms,
            created_at=self.orchestration_input.created_at,
            sources_path=self.orchestration_input.sources_path,
            packet_draft_path=self.orchestration_input.packet_draft_path,
            evidence_limits=self.orchestration_input.evidence_limits,
        )

        result = orchestrate_run(input_uncertain, self.output_dir)
        saved = json.loads(result.summary_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_after, "HOLD")
        self.assertEqual(result.result, "HOLD")
        self.assertEqual(saved["completed_operations"], ["O-01", "O-02", "O-03"])
        self.assertEqual(saved["stop_reason"], "SCREENING_HOLD")
        self.assertEqual(saved["resume_position"], "O-03")
        self.assertEqual(saved["next_action"], "O-03 Safety Screenを再実行して再開する")

    def test_repeated_run_is_idempotent(self) -> None:
        first = orchestrate_run(self.orchestration_input, self.output_dir)
        second = orchestrate_run(self.orchestration_input, self.output_dir)

        self.assertTrue(first.changed)
        self.assertFalse(second.changed)
        self.assertEqual(second.summary_path.stat().st_mtime_ns, first.summary_path.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
