# Knowledge Harness Operations

## 状態の正本

- Phase 0では[GitHub Issue #2](https://github.com/mtakagishi/note/issues/2)を公開可能な継続状態の正本とする
- `STATUS.md`はリポジトリ内の状態スナップショットとする
- 会話履歴やセッション要約を作業状態の正本にしない
- 作業開始時はIssue本文、最新HANDOFF、`STATUS.md`の順に確認し、矛盾があれば作業を止める

## 作業開始

着手前に次の三点を日本語で要約する。

1. 今回行う一件
2. 変更対象
3. 停止条件

一度のセッションで扱う「次の一手」は一件だけとし、未承認の次フェーズへ進まない。

## 状態更新

- 完了後、検証結果を記録してから次の一手を一件だけ設定する
- `STATUS.md`とIssue本文の現在地、次の一手、ブロッカーを一致させる
- 新しい恒久判断は`DECISIONS.md`へ追記する
- 途中で中断する場合も、未完了状態と再開地点を隠さない
- 失敗した作業を完了扱いにせず、失敗原因と次の試行点を残す
- 私的情報、会社情報、非公開会話を公開Issueや公開文書へ記録しない

## HANDOFF

セッション終了時はIssue #2へ次の形式のコメントを一件追加する。

```markdown
## HANDOFF YYYY-MM-DD

### 完了
- ...

### 決定
- ...

### 検証
- ...

### 未完了
- ...

### 次の一手
- 一件だけ記載する

### ブロッカー
- なし / ...

### 関連
- Issue / PR / branch / commit / file
```

## 再開プロンプト

### ChatGPT / Codex Work

```text
mtakagishi/note のIssue #2を継続状態の正本として読み、最新のHANDOFF、STATUS.md、「次の一手」から作業を再開してください。
着手前に、今回行う一件、変更対象、停止条件を要約してください。
既存の私的な会話履歴を推測・要約して入力に使わないでください。
```

### VS Code

```text
このリポジトリのIssue #2を継続状態の正本として読み、最新のHANDOFF、STATUS.md、「次の一手」から作業を再開してください。
今回の作業は一件に限定し、完了時にSTATUSとHANDOFFを更新してください。
未承認の次フェーズへ進まないでください。
```

## 不一致や判断待ち

- Issue、最新HANDOFF、`STATUS.md`に不一致がある場合は変更を始めない
- 新しい判断が必要な場合は、選択肢と影響を示して人間の判断を待つ
- 人間が応答しない場合は公開せず保留し、許可された他の処理だけを継続する

## 記事処理パイプラインとの境界

- この文書は、作業セッションの中断、再開、状態同期だけを扱う
- 記事候補の受付から公開判断までの状態遷移とOperation契約は`PIPELINE.md`を正とする
- パイプライン実行中の状態は成果物として保存し、会話履歴だけに保持しない

## O-13 Record Outcomeの実行

O-13はパイプラインの終了または引き継ぎ時に、状態、理由、成果物、検証結果、次の一手を保存する。次のように実行する。

```powershell
rye run python -m note.knowledge_harness.outcomes `
  --run-id run-20260811-001 `
  --state-before VALIDATED `
  --state-after REVIEW_READY `
  --result ADVANCE `
  --reason-code DRAFT_PR_READY `
  --summary-ja "Draft PRを作成し、公開判断を待てる状態になりました。" `
  --producer program `
  --input-ref issue:2 `
  --artifact-ref pr:6 `
  --verification-ref unittest:pass `
  --next-action "人間がDraft PRを確認する" `
  --human-action publication
```

既定では`_notes/knowledge_harness/outcomes/<run_id>/`に`outcome.json`と`HANDOFF.md`を保存し、`_notes/knowledge_harness/outcomes/metrics.json`を再集計する。このディレクトリは実行時成果物のためGit管理しない。

- 同じ`run_id`の再実行では記録を重複させず、内容が変わった場合だけ更新する
- `--created-at`を省略した再実行では既存の記録時刻を維持する
- `--human-action`は`none`、`publication`、`policy`、`privacy`、`exception`から選ぶ
- Metricsは反復する人間判断を見つける材料とし、`DECISIONS.md`を自動更新しない

検証には次を使う。

```powershell
rye run python -m unittest discover -s tests -p "test_*.py"
rye run ruff check src/note/knowledge_harness tests/test_record_outcome.py
```

## O-01 Capture Requestの実行

O-01は公開可能な「知りたいこと」を共通形式のRequestへ変換する。公開Issueは公開可能と扱い、許可済みの別入力は`approved_input`を指定する。

```powershell
rye run python -m note.knowledge_harness.capture_request `
  --run-id run-20260811-002 `
  --question-ja "公開Issueから記事候補を安全に受け付けるには？" `
  --source-ref issue:7 `
  --source-kind public_issue
```

既定では`_notes/knowledge_harness/requests/<run_id>/request.json`へ保存する。

- `public_issue`と`approved_input`は`CAPTURED / ADVANCE`とする
- `unconfirmed_input`は`HOLD`とし、公開可能性だけを人間へ確認する
- 問いが空の場合は、記事内容を推測せず入力エラーとする
- 同じ`run_id`の再実行では重複させず、内容が変わった場合だけ更新する
- O-01はO-02以降を自動実行しない

## O-02 Authorize Runの実行

O-02はO-01が生成したRequestと現在のラベル一覧を受け取り、明示的な実行ラベルがある場合だけ後続処理を許可する。

```powershell
rye run python -m note.knowledge_harness.authorize_run `
  --request-file _notes/knowledge_harness/requests/run-20260811-002/request.json `
  --label knowledge-harness:run
```

既定では`_notes/knowledge_harness/authorized/<run_id>/authorization.json`へ保存する。

- 既定の実行ラベルは`knowledge-harness:run`とする
- 別のラベルを使う場合は`--required-label`で変更できる
- 必須ラベルがあれば`AUTHORIZED / ADVANCE`とする
- 必須ラベルがなければ`CAPTURED / HOLD`とし、状態を進めない
- ラベルがない場合は人間へ質問や催促を行わない
- O-01が`HOLD`にしたRequestはラベルがあっても許可しない
- 同じ`run_id`へラベルを追加して再実行した場合は、既存記録を更新する

## O-03 Screen Safetyの実行

O-03は許可済みRequestを決定的な規則で検査し、安全な情報だけを後続へ渡す。

```powershell
rye run python -m note.knowledge_harness.screen_safety `
  --authorization-file _notes/knowledge_harness/authorized/run-20260811-002/authorization.json
```

既定では`_notes/knowledge_harness/screened/<run_id>/screening.json`へ保存する。

- 秘密鍵、代表的なアクセストークン、秘密値の代入を検出した場合は`REJECTED`とする
- `社外秘`、`部外秘`、`非公開会話`などの明確な非公開マーカーを検出した場合は`REJECTED`とする
- 固有の非公開語は`--restricted-term`で追加できる
- メールアドレスと電話番号はマスクし、マスク後のRequestだけを`SCREENED`として渡す
- 拒否した入力本文は成果物へ複製しない
- 自動判定不能と分かっている場合は`--assessment uncertain`で本文を保持せず`HOLD`とし、公開可能性だけを確認する
- 明確に非公開と分かっている場合は`--assessment private`で質問せず`REJECTED`とする
- O-02が待機中のAuthorizationは検査しない

## O-04 Collect Evidenceの実行

O-04はO-03を通過したRequestと、検索で発見した公開情報源候補を受け取り、本文を取得してEvidence Setを作る。外部検索サービスとの本格連携はPhase 6のスコープ外であるため、検索結果はJSONマニフェストとして渡す。

```powershell
rye run python -m note.knowledge_harness.collect_evidence `
  --screening-file _notes/knowledge_harness/screened/run-20260811-002/screening.json `
  --sources-file sources.json
```

`sources.json`は次の形式にする。

```json
{
  "sources": [
    {
      "url": "https://example.com/official-document",
      "source_type": "primary",
      "title": "公式文書",
      "publisher": "Example",
      "published_at": "2026-08-11",
      "target_version": "1.0",
      "summary_ja": "確認対象となる公式説明の要約",
      "supports": ["確認できた事実"],
      "limitations": ["この資料だけでは確認できない事項"],
      "confidence": "high",
      "confidence_reason": "公式文書であるため",
      "search_round": 1,
      "query": "example 公式文書",
      "topics": ["対象仕様"],
      "uncertainties": [],
      "contradictions": []
    }
  ]
}
```

既定では`_notes/knowledge_harness/evidence/<run_id>/evidence.json`へ保存する。

- `source_type`は`primary`、`secondary`、`community`、`discovery_only`から選ぶ
- URLは公開HTTP(S)だけを受け付け、認証やアクセス制限を回避しない
- 取得本文そのものは保存せず、SHA-256、バイト数、Content-Typeと提供された該当箇所・要約を保存する
- URL断片を除いた同一URLを重複排除し、同一ドメインからの採用は3件までとする
- 検索3ラウンド、各4クエリ、取得20回、採用12件、15分を初期上限とする
- 一時的な失敗は追加2回まで再試行し、恒久的失敗とともに理由を保存する
- 必要範囲を確認できた候補へ`"complete_scope": true`を指定すると、取得成功後に早期終了する
- 1件以上取得できれば、不足や矛盾があっても`EVIDENCE_READY / ADVANCE`とする
- 一時的失敗だけなら`SCREENED / RETRYABLE_ERROR`、全面的に取得不能なら`HOLD`とする
- 同じ入力と同じ取得内容では成果物を書き換えない

O-04のMetricsをO-13へ集計する場合は、Evidence Set自体をMetrics入力として指定する。

```powershell
rye run python -m note.knowledge_harness.outcomes `
  --run-id run-20260811-002 `
  --state-before SCREENED `
  --state-after EVIDENCE_READY `
  --result ADVANCE `
  --reason-code EVIDENCE_COLLECTED `
  --summary-ja "公開情報を取得し、不足と矛盾を含むEvidence Setを記録しました。" `
  --producer program `
  --source-operation O-04 `
  --operation-metrics-file _notes/knowledge_harness/evidence/run-20260811-002/evidence.json `
  --artifact-ref _notes/knowledge_harness/evidence/run-20260811-002/evidence.json `
  --next-action "O-05 Build Evidence Packetへ渡す" `
  --human-action none
```

O-13は数値MetricsをOperation別に合計する。初期上限の変更は自動採用せず、原則10実行分を人間が確認する。

## O-05 Build Evidence Packetの実行

O-05はSkill / AgentがEvidence Setを読んで作った整理案を、Programで出典検証してEvidence Packetへ保存する。意味整理と決定的な検証を分け、AIが存在しない根拠を追加できないようにする。

```powershell
rye run python -m note.knowledge_harness.build_evidence_packet `
  --evidence-file _notes/knowledge_harness/evidence/run-20260811-002/evidence.json `
  --draft-file packet-draft.json
```

`packet-draft.json`は次の形式にする。

```json
{
  "summary_ja": "取得済み根拠を論点別に整理しました。",
  "topics": [
    {
      "topic_id": "topic-001",
      "title_ja": "仕様と利用者評価",
      "items": [
        {
          "item_id": "item-001",
          "kind": "fact",
          "statement_ja": "公式仕様に対象機能が記載されています。",
          "source_ids": ["source-001"],
          "notes_ja": "対象バージョンを限定して扱います。"
        },
        {
          "item_id": "item-002",
          "kind": "contradiction",
          "statement_ja": "公式仕様と利用者報告に差があります。",
          "source_ids": ["source-001", "source-003"]
        }
      ]
    }
  ],
  "past_articles": {
    "article_refs": ["blog:2026-example"],
    "known_items": [],
    "difference_candidates": [],
    "recheck_items": []
  }
}
```

既定では`_notes/knowledge_harness/packets/<run_id>/evidence_packet.json`へ保存する。

- `kind`は`fact`、`inference`、`unconfirmed`、`community_reaction`、`contradiction`から選ぶ
- すべての記述へEvidence Setに実在する`source_id`を一件以上指定する
- `contradiction`には異なる根拠を二件以上指定する
- `community_reaction`には`secondary`または`community`情報源を一件以上含める
- `item_id`と`topic_id`はそれぞれPacket内で一意にする
- 説明が空、出典が存在しない、分類条件を満たさない整理案は保存しない
- 過去記事参照がない場合、既知事項と差分候補を作らず`UNCONFIRMED_NO_PAST_ARTICLE`とする
- Evidence Setの取得失敗、不確実性、Metricsを欠落させずPacketへ継承する
- 同じEvidence Setと整理案の再実行では成果物を書き換えない
- O-05は新しい情報取得、矛盾の解消、根拠充足性や記事候補の採否判断を行わない

## O-06 Judge Candidateの実行

O-06はAI JudgeがEvidence Packetを5軸で評価した判定案をProgramで検証し、記事候補の採否をCandidate Decisionへ保存する。

```powershell
rye run python -m note.knowledge_harness.judge_candidate `
  --packet-file _notes/knowledge_harness/packets/run-20260811-002/evidence_packet.json `
  --judgment-file candidate-judgment.json
```

`candidate-judgment.json`は次の形式にする。5評価軸すべてに、判定、確信度、理由、Evidence Packet内の参照項目を指定する。

```json
{
  "rubric_version": "candidate-v1",
  "judge_id": "judge-example",
  "evaluations": {
    "evidence_sufficiency": {
      "verdict": "PASS",
      "confidence": 0.9,
      "reason_ja": "中心論点を一次情報が支えています。",
      "packet_refs": ["topics/topic-001/items/item-001"]
    },
    "novelty": {
      "verdict": "PASS",
      "confidence": 0.8,
      "reason_ja": "過去記事との差分候補を確認できます。",
      "packet_refs": ["past_articles/difference_candidates/item-002"]
    },
    "reader_value": {
      "verdict": "PASS",
      "confidence": 0.8,
      "reason_ja": "外部読者が手順を転用できます。",
      "packet_refs": ["summary_ja"]
    },
    "author_specific_question": {
      "verdict": "PASS",
      "confidence": 0.9,
      "reason_ja": "著者の問いをRequestから復元できます。",
      "packet_refs": ["screened_request"]
    },
    "uncertainty_impact": {
      "verdict": "PASS",
      "confidence": 0.8,
      "impact": "MEDIUM",
      "reason_ja": "未確認範囲は中心論点を覆しません。",
      "packet_refs": ["uncertainties/0"]
    }
  }
}
```

既定では`_notes/knowledge_harness/decisions/<run_id>/candidate_decision.json`へ保存する。

- `verdict`は`PASS`、`FAIL`、`UNCERTAIN`、`impact`は`LOW`、`MEDIUM`、`HIGH`から選ぶ
- Packet参照は`topics/<topic_id>/items/<item_id>`など、実在する項目だけを受け付ける
- 必須4軸のいずれかが`FAIL`なら`NO_CANDIDATE / NO_CANDIDATE`として正常終了する
- 必須軸に`UNCERTAIN`がある、または不確実性の影響が`HIGH`なら`HOLD / HOLD`とする
- 確信度0.70未満の`PASS`はProgramが`UNCERTAIN`へ正規化する
- 過去記事との比較がない場合、新規性の`PASS`は`UNCERTAIN`へ正規化する
- 全必須軸が確信度0.70以上の`PASS`で、不確実性の影響が`LOW`または`MEDIUM`の場合だけ`CANDIDATE_ACCEPTED / ADVANCE`とする
- 非採用と保留では人間へ質問せず、根拠不足を補完しない
- 同じPacketと判定案の再実行では成果物を書き換えない
- O-06はO-07以降の記事計画や本文生成を実行しない
