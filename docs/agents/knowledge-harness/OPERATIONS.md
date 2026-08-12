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

着手宣言の最初に、今回の議題種別を次のどちらか一つで明示する。

- ① 優良記事作成（記事単位の処理、公開可否、改稿）
- ② 方法論改善（Operation契約、再開手順、回帰テスト、運用規約）

一度のセッションで扱う「次の一手」は一件だけとし、未承認の次フェーズへ進まない。

同一セッションで①と②を同時に扱わない。途中で混在が発生した場合は、その時点で作業を分割し、今回の一件を完了または中断記録してから次の議題へ移る。

分割の基準は、対象が記事1本の状態遷移か、方法論の定義・運用・回帰テストかで区別する。記事関連の判断は`PIPELINE.md`と`run_id`成果物を正本にして本文を変えず、方法論改善のみを`STATUS.md`と`OPERATIONS.md`で管理する。

## 再開時の半自動化境界

- 中レベル半自動化では、状態収集、差分有無確認、次の一手の提案までを自動化対象とする
- 議題種別の暗黙決定、公開承認、恒久方針の採用は自動化対象に含めない
- 公開可否に関わる操作は必ず人間判断を通し、無回答または曖昧な場合は`HOLD`を優先する
- 必須情報欠落、Issueと`STATUS.md`の不一致、議題種別不一致を検出した場合は処理を停止し、人間確認へ切り替える

### 半自動化I/O契約

- 入力は、議題種別、`_notes/sessions/resume-handoff-latest.md`、最小確認の参照範囲5点に限定する
- 出力は、確認結果5点、不一致または不足の有無、次の最初の作業1件に限定する
- 半自動化の出力は提案であり、公開承認、恒久方針採用、議題種別決定を代替しない
- 停止時は、停止理由、不足情報、再開条件を日本語で記録し、手動最小確認へ戻す
- 停止理由が同一で再発する場合は、再発防止の回帰観点を`STATUS.md`の次の一手に反映する

### 半自動化の実行ログ運用

- 確認専用コマンドテンプレートを実行した場合は、同一ターン内で実行ログを記録する
- 記録項目は、実行時刻（JST）、議題種別、確認結果5点、停止有無、再開条件、次の最初の作業1件とする
- 停止が発生した場合は、停止理由と再開条件を`_notes/sessions/resume-handoff-latest.md`へ反映する
- 停止がない場合でも、確認結果5点の要約を残し、次の最初の作業を一件だけ更新する
- 実行ログは公開可能な情報だけで構成し、私的情報、会社情報、非公開会話を含めない

記入揺れを避けるため、次の補正ルールを固定する。

1. 実行時刻は`YYYY-MM-DD HH:MM JST`で統一する
2. main差分は`left-right-count`と意味（main側先行 / 作業側先行）を併記する
3. ブランチ状態は`ブランチ名 + clean/dirty`で記録する
4. open issueは起点issue番号を必須記録にする
5. 停止なしの場合は`再開条件: 不要`を記録する

確認専用の機械実行テンプレートは次を使う。

```powershell
git status --short --branch
gh issue list --state open --limit 20
gh pr list --state merged --limit 5
git rev-list --left-right --count main...HEAD
git branch --show-current
```

### 停止系の回帰観点

`stop_reason`と`next_action`の正本は`src/note/knowledge_harness/orchestrate_run.py`とし、この文書は運用時の確認観点だけを保持する。

| stop_reason | resume_position | 回帰観点 | 期待される次の一手 |
| --- | --- | --- | --- |
| REQUEST_HOLD | O-01 | 問いの必須情報不足時に停止し、推測補完しない | O-01入力を補完して再開 |
| RUN_LABEL_MISSING | O-02 | 実行ラベル不足時に停止し、催促しない | O-02入力を補完して再開 |
| SCREENING_HOLD | O-03 | 公開可否が自動判定不能なら停止し、人間確認へ回す | O-03再実行で再開 |
| EVIDENCE_INPUT_MISSING | O-04 | sources入力不足時に停止し、探索を拡大しない | O-04入力を補完して再開 |
| EVIDENCE_COLLECTION_HOLD | O-04 | 収集不能や根拠不足で停止し、仮説で埋めない | O-04再実行で再開 |
| PACKET_DRAFT_MISSING | O-05 | Evidence Set欠落時に停止し、新規取得で穴埋めしない | O-05入力を補完して再開 |
| PACKET_BUILD_HOLD | O-05 | 整理不能時に停止し、採否判定へ進めない | O-05再実行で再開 |
| JUDGMENT_INPUT_MISSING | O-06 | 候補判定入力不足時に停止し、閾値を変更しない | O-06入力を補完して再開 |
| CANDIDATE_DECISION_HOLD | O-06 | 評価が確定不能なら停止し、公開側へ進めない | O-06再実行で再開 |
| PLAN_DRAFT_MISSING | O-07 | 計画入力不足時に停止し、本文生成へ進めない | O-07入力を補完して再開 |
| PLAN_ARTICLE_HOLD | O-07 | 著者判断不足で停止し、推測で主旨確定しない | O-07再実行で再開 |
| DRAFT_PROPOSAL_MISSING | O-08 | 下書き入力不足時に停止し、未計画節を追加しない | O-08入力を補完して再開 |
| DRAFT_ARTICLE_HOLD | O-08 | Draft生成条件未達で停止し、公開配置しない | O-08再実行で再開 |
| VALIDATION_JUDGMENT_MISSING | O-09 | 検証入力不足時に停止し、意味改稿で誤魔化さない | O-09入力を補完して再開 |
| VALIDATION_HOLD | O-09 | ProgramまたはJudgeで不合格なら停止し、公開へ進めない | O-09再実行で再開 |
| REVIEW_PROPOSAL_MISSING | O-10 | Review入力不足時に停止し、判断選択肢を欠落させない | O-10入力を補完して再開 |
| PREPARE_REVIEW_HOLD | O-10 | Review準備不能時に停止し、最終判断へ進めない | O-10再実行で再開 |
| PUBLICATION_DECISION_INPUT_MISSING | O-11 | 公開判断入力不足時に停止し、承認を推定しない | O-11入力を補完して再開 |
| PUBLICATION_DECISION_HOLD | O-11 | 判断矛盾・無回答時に停止し、公開しない | O-11再実行で再開 |
| FEEDBACK_PROPOSAL_MISSING | O-12 | 修正指示不足時に停止し、未指定改稿しない | O-12入力を補完して再開 |
| APPLY_FEEDBACK_HOLD | O-12 | 修正上限超過または境界違反で停止し、無限改稿しない | O-12再実行で再開 |

回帰観点を更新する場合は、`tests/test_orchestrate_run.py`の停止系テストを同時更新し、文言だけの変更で挙動を変えない。

## 状態更新

- 完了後、検証結果を記録してから次の一手を一件だけ設定する
- `STATUS.md`とIssue本文の現在地、次の一手、ブロッカーを一致させる
- 新しい恒久判断は`DECISIONS.md`へ追記する
- `STATUS.md`へは方法論進捗だけを記録し、記事個別のHOLD理由や改稿指示は`run_id`成果物へ記録する
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
最初に今回の議題種別を「①優良記事作成」または「②方法論改善」のどちらか一つで宣言してください。
着手前に、今回行う一件、変更対象、停止条件を要約してください。
既存の私的な会話履歴を推測・要約して入力に使わないでください。
```

### VS Code

```text
このリポジトリのIssue #2を継続状態の正本として読み、最新のHANDOFF、STATUS.md、「次の一手」から作業を再開してください。
最初に今回の議題種別を「①優良記事作成」または「②方法論改善」のどちらか一つで宣言してください。
今回の作業は一件に限定し、完了時にSTATUSとHANDOFFを更新してください。
未承認の次フェーズへ進まないでください。
```

## 不一致や判断待ち

- Issue、最新HANDOFF、`STATUS.md`に不一致がある場合は変更を始めない
- 新しい判断が必要な場合は、選択肢と影響を示して人間の判断を待つ
- 人間が応答しない場合は公開せず保留し、許可された他の処理だけを継続する
- 半自動化の再開補助が失敗した場合は、手動の最小確認手順へ戻して確認結果を残す

## 記事処理パイプラインとの境界

- この文書は、作業セッションの中断、再開、状態同期だけを扱う
- 記事候補の受付から公開判断までの状態遷移とOperation契約は`PIPELINE.md`を正とする
- 探索対象の開始条件は利用者が明示した知りたい情報と承認済み実行ラベルとし、探索上限はO-04契約に従う
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

## O-07 Plan Articleの実行

O-07はSkill / Agentが作る計画案をProgramで検証し、O-08が新しい事実や意図を追加せず展開できるArticle Planへ保存する。

```powershell
rye run python -m note.knowledge_harness.plan_article `
  --decision-file _notes/knowledge_harness/decisions/run-20260811-002/candidate_decision.json `
  --packet-file _notes/knowledge_harness/packets/run-20260811-002/evidence_packet.json `
  --draft-file article-plan-draft.json
```

通常の`article-plan-draft.json`は次の形式にする。

```json
{
  "mode": "PLAN",
  "plan_version": "article-plan-v1",
  "planner_id": "planner-example",
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
      "packet_refs": ["topics/topic-001/items/item-001"]
    }
  ],
  "excluded_topics": [
    {
      "topic_ja": "対象外の版",
      "reason_ja": "根拠を確認できないためです。"
    }
  ],
  "uncertainty_treatments": [
    {
      "packet_ref": "uncertainties/0",
      "action": "DISCLOSE",
      "reason_ja": "適用範囲を読者へ明示するためです。"
    }
  ]
}
```

既定では`_notes/knowledge_harness/plans/<run_id>/article_plan.json`へ保存する。

- 同じ`run_id`の`CANDIDATE_ACCEPTED / ADVANCE`と`PACKET_READY / ADVANCE`だけを受け付ける
- 構成型は`TUTORIAL`、`CONCEPT_EXPLANATION`、`CHANGE_ANALYSIS`、`TROUBLESHOOTING`、`DECISION_RECORD`から選ぶ
- 各節に一意なID、見出し、目的、読者が得るもの、実在するPacket参照を指定する
- Evidence Packetのすべての不確実性に`DISCLOSE`、`LIMIT_CLAIM`、`EXCLUDE`の扱いと理由を指定する
- 正常な計画は`PLAN_READY / ADVANCE`とし、人間へ質問しない
- 同じ入力の再実行では成果物を書き換えない

著者固有の動機が中心メッセージに不可欠で、Packetから復元できない場合だけ`mode`を`AUTHOR_QUESTION`にする。

```json
{
  "mode": "AUTHOR_QUESTION",
  "plan_version": "article-plan-v1",
  "planner_id": "planner-example",
  "question_reason_ja": "著者固有の動機を中心メッセージに反映するためです。",
  "questions": [
    {
      "question_id": "question-001",
      "question_kind": "AUTHOR_MOTIVATION",
      "question_ja": "この変更を調べたきっかけは何ですか？",
      "purpose_ja": "記事の中心となる著者の動機を確認します。",
      "packet_refs": ["screened_request"]
    }
  ]
}
```

- 質問は一回、最大3問、`AUTHOR_MOTIVATION`だけに限定し、`HOLD / HOLD`とする
- 技術的事実、根拠不足、構成の好みを質問しない
- 保存後に質問を別内容へ差し替えない
- 回答後に`PLAN`へ進む場合は、公開可能な回答の参照を`author_context_ref`へ指定する
- 回答がなくても安全な計画を作れる場合は質問せず、不確実性の扱いを指定して進める
- O-07は記事本文、reStructuredText、英訳、画像、最終タイトル、公開日を生成・確定しない

## O-08 Draft Articleの実行

O-08はSkill / Agentが作る節別本文案をProgramで検証し、日本語reStructuredTextのDraftとPacket参照manifestへ保存する。

```powershell
rye run python -m note.knowledge_harness.draft_article `
  --plan-file _notes/knowledge_harness/plans/run-20260811-002/article_plan.json `
  --packet-file _notes/knowledge_harness/packets/run-20260811-002/evidence_packet.json `
  --proposal-file article-draft-proposal.json
```

`article-draft-proposal.json`は次の形式にする。

```json
{
  "draft_version": "article-draft-v1",
  "drafter_id": "drafter-example",
  "sections": [
    {
      "section_id": "section-001",
      "blocks": [
        {
          "block_id": "block-001",
          "body_rst": "公式情報で確認できる変更点を説明します。",
          "packet_refs": ["topics/topic-001/items/item-001"]
        },
        {
          "block_id": "block-002",
          "body_rst": "対象バージョンの一部は未確認です。",
          "packet_refs": ["uncertainties/0"]
        }
      ]
    }
  ]
}
```

既定では次の中間成果物を保存する。

- `_notes/knowledge_harness/drafts/<run_id>/draft.rst`
- `_notes/knowledge_harness/drafts/<run_id>/draft_manifest.json`

検証と生成の規則は次のとおり。

- 同じ`run_id`の`PLAN_READY / ADVANCE`と`PACKET_READY / ADVANCE`だけを受け付ける
- Article Planの全節を同じIDと順序で一回ずつ指定する
- 各節に一件以上の本文ブロックを指定し、`block_id`はDraft全体で一意にする
- 本文ブロックのPacket参照は、そのPlan節で許可された参照だけに限定する
- 各節の計画済み参照を少なくとも一つの本文ブロックへ対応付ける
- `DISCLOSE`と`LIMIT_CLAIM`の不確実性を本文で使用し、`EXCLUDE`対象は使用しない
- `raw`、`include`、`literalinclude`、`image`、`figure`、`post` directiveを本文ブロックへ含めない
- 本文ブロック内にPlan外のreStructuredText見出しを追加しない
- manifestへ各ブロックの節ID、Packet参照、SHA-256を保存する
- Draft冒頭に記事状態、未確定の公開日、情報基準日、対象バージョン、生成動機、AI担当範囲、人間の確認範囲を表示する
- Packetに対象バージョンがなければ推測せず`未確認`とする
- 公開用`post` directiveを生成せず、`docs/blog/posts/`への出力を拒否する
- 同じ入力の再実行では`draft.rst`とmanifestを書き換えない
- O-08は人間へ質問せず`DRAFT_READY / ADVANCE`とする
- 事実性、意味の飛躍、読者価値、構成品質、リンク、ビルド、秘密情報はO-09で検証する

## O-09 Validate Draftの実行

O-09はO-08のDraftをProgramとAI Judgeで検証し、修正済みDraftとValidation Reportを中間成果物として保存する。

```powershell
rye run python -m note.knowledge_harness.validate_draft `
  --draft-file _notes/knowledge_harness/drafts/run-20260811-002/draft.rst `
  --manifest-file _notes/knowledge_harness/drafts/run-20260811-002/draft_manifest.json `
  --plan-file _notes/knowledge_harness/plans/run-20260811-002/article_plan.json `
  --packet-file _notes/knowledge_harness/packets/run-20260811-002/evidence_packet.json `
  --judgment-file draft-validation-judgment.json
```

`draft-validation-judgment.json`は次の形式にする。5評価軸すべてに判定、確信度、理由、実在するDraftブロックとPacket項目の参照を指定する。

```json
{
  "rubric_version": "draft-validation-v1",
  "judge_id": "judge-example",
  "evaluations": {
    "factual_grounding": {
      "verdict": "PASS",
      "confidence": 0.9,
      "reason_ja": "記述が指定した根拠の範囲内です。",
      "block_ids": ["block-001"],
      "packet_refs": ["topics/topic-001/items/item-001"]
    },
    "semantic_leap": {
      "verdict": "PASS",
      "confidence": 0.9,
      "reason_ja": "根拠から結論への飛躍はありません。",
      "block_ids": ["block-001"],
      "packet_refs": ["topics/topic-001/items/item-001"]
    },
    "reader_value": {
      "verdict": "PASS",
      "confidence": 0.8,
      "reason_ja": "計画した読者価値を本文で伝えています。",
      "block_ids": ["block-001"],
      "packet_refs": ["topics/topic-001/items/item-001"]
    },
    "plan_alignment": {
      "verdict": "PASS",
      "confidence": 0.9,
      "reason_ja": "Article Planに沿っています。",
      "block_ids": ["block-001"],
      "packet_refs": ["topics/topic-001/items/item-001"]
    },
    "uncertainty_handling": {
      "verdict": "PASS",
      "confidence": 0.8,
      "reason_ja": "未確認事項を明示しています。",
      "block_ids": ["block-002"],
      "packet_refs": ["uncertainties/0"]
    }
  },
  "policy_change_candidate": { "required": false }
}
```

既定では次の中間成果物を保存する。

- `_notes/knowledge_harness/validations/<run_id>/validated_draft.rst`
- `_notes/knowledge_harness/validations/<run_id>/validation_report.json`

検証と判定の規則は次のとおり。

- 同じ`run_id`の`DRAFT_READY / ADVANCE`、Article Plan、Evidence Packetだけを受け付ける
- 元DraftとmanifestのSHA-256、節順、ブロック本文・SHA-256・Packet参照の整合性を検査する
- reStructuredText構文、必須metadata、外部・ローカルリンク、秘密情報、個人情報、非公開マーカーを検査する
- 外部URLはEvidence Packetの`source_catalog`に記録されたURLだけを許可する
- 既存記事との正規化タイトル一致はError、正規化本文の類似度0.85以上はWarning候補とする
- 末尾空白、最終改行、生成された見出し装飾長だけを一回自動修正し、O-08の入力Draftは変更しない
- AI Judgeの判定は`PASS`、`FAIL`、`UNCERTAIN`とし、確信度0.70未満の`PASS`は`UNCERTAIN`へ正規化する
- Program Errorがなく、5評価軸がすべて確信度0.70以上の`PASS`なら`VALIDATED / ADVANCE`とする
- Program Error、AI Judgeの非`PASS`、または恒久方針変更候補があれば`HOLD / HOLD`とし、公開へ進めない
- 機械用の状態・結果コードは維持し、人間向けには`human_guidance_ja`で状態名、結果の意味、判断要否、求める判断、無回答時の扱いを日本語表示する
- `VALIDATED / ADVANCE`は「検証合格：次の工程へ進めます」を意味し、公開承認や公開完了を意味しない
- 通常の検証不合格は「検証不合格：問題があるため保留します」と表示し、人間へ根拠補完や例外判断を求めない
- 恒久方針変更候補がある場合は「方針判断待ち：判断があるまで保留します」と表示し、選択肢と影響の確認を日本語で求める
- 恒久方針変更が本当に必要な場合だけ、問題と2件以上3件以下の選択肢・影響を保存し、人間の`policy`判断を要求する
- Warningだけでは停止せずValidation Reportへ残す
- 同じ入力の再実行では成果物を書き換えない
- O-09は新しい調査、意味を変える本文修正、公開配置、英訳、画像生成を行わない

## O-10 Prepare Reviewの実行

O-10は検証済みDraftへ公開用metadataを付け、日本語Review PacketとDraft PR準備情報を保存する。O-10自身はGitHub認証、commit、push、PR作成、mergeを実行しない。

```powershell
rye run python -m note.knowledge_harness.prepare_review `
  --validated-draft-file _notes/knowledge_harness/validations/run-20260811-002/validated_draft.rst `
  --validation-report-file _notes/knowledge_harness/validations/run-20260811-002/validation_report.json `
  --plan-file _notes/knowledge_harness/plans/run-20260811-002/article_plan.json `
  --packet-file _notes/knowledge_harness/packets/run-20260811-002/evidence_packet.json `
  --proposal-file review-proposal.json
```

`review-proposal.json`は次の形式にする。

```json
{
  "review_version": "review-v1",
  "preparer_id": "preparer-example",
  "final_title_ja": "変更を安全に確認する方法",
  "slug": "safe-change-review",
  "tags": ["運用", "検証"],
  "category_ja": "運用改善",
  "author": "mtakagishi"
}
```

既定では次の成果物を保存する。

- `docs/blog/posts/YYYY-MM-DD-slug.rst`
- `_notes/knowledge_harness/reviews/<run_id>/review_packet.json`

検証と生成の規則は次のとおり。

- 同じ`run_id`の`VALIDATED / ADVANCE`、修正済みDraft、Article Plan、Evidence Packetだけを受け付ける
- 修正済みDraftのSHA-256をValidation Reportと照合する
- `slug`は小文字英数字をハイフンで区切り、タグは空・重複を許可しない
- Asia/Tokyo基準の実行日より後で、既存ファイル名と`post` directiveに使われていない最初の日を公開日にする
- 再実行時は同じ`run_id`のReview Packetに保存した公開日を再利用する
- 検証済み本文の意味を変更せず、最終タイトル、`post` directive、公開候補状態、公開日だけを反映する
- `post` directiveにはタグ、カテゴリ、著者、`:language: ja`を付ける
- Review Packetへ公開候補と全入力のパス・SHA-256、中心メッセージ、根拠参照、不確実性、検証結果を保存する
- 人間向け状態は「公開候補の確認待ち」とし、まだ公開承認されていないことを日本語で説明する
- 「公開を承認する」「今回だけ修正を求める」「公開しない」「今後の方針として検討する」の4選択肢と影響を日本語で示す
- 回答がない場合は公開せず保留することを明記する
- `pr_preparation.dedupe_key`を`run_id`とし、一実行につき一つのDraft PRを外側の実行主体が作れる情報を保存する
- 正常時は`REVIEW_READY / ADVANCE`とし、`required_human_action`を`publication`とする
- 同じ入力の再実行では公開候補とReview Packetを書き換えない
- O-10は本文修正、新しい調査、英訳、画像、レビュー判断、公開承認を行わない

## O-11 Decide Publicationの実行

O-11は外側のGitHub実行主体が取得したPR snapshotと、人間が日本語表示から選んだ構造化判断を検証し、Publication Decisionを保存する。GitHub操作自体は行わない。

```powershell
rye run python -m note.knowledge_harness.decide_publication `
  --review-packet-file _notes/knowledge_harness/reviews/run-20260811-002/review_packet.json `
  --article-file docs/blog/posts/2026-08-12-safe-change-review.rst `
  --pr-snapshot-file publication-pr.json `
  --human-decision-file publication-decision-input.json `
  --repository mtakagishi/note `
  --pr-number 99 `
  --base main `
  --authorized-actor mtakagishi
```

PR snapshotには`repository`、`number`、`base`、`head`、`head_sha`、`url`、`merged`、`merged_by`、`merge_commit_sha`を含める。人間判断は`decisions`配列へ一件だけ指定し、`decision`は`revision`、`reject`、`policy_candidate`のいずれかとする。判断者、日時、理由、参照URL・ID、対象commit SHAを必須とする。

- merge済みPRでは人間判断ファイルを渡さず、許可actorの`merged_by`と`merge_commit_sha`を確認して`APPROVED / ADVANCE`とする
- 修正要求は`instruction_ja`、`target_ja`を必須とし、`REVISION / ADVANCE`でO-12へ渡す
- 棄却は`HOLD / HOLD`でO-13へ渡し、追加の人間判断を要求しない
- 恒久方針候補は問題と2〜3選択肢・影響を必須とし、公開せず`HOLD / HOLD`とする
- 無回答、複数判断、mergeとの矛盾、対象外actor、対象commit不一致は公開せず`HOLD / HOLD`とする
- 自由文を判断種別へ推測変換せず、対象PRのrepository、番号、base、head、記事SHA-256を照合する
- 結果の意味と次の処理は`human_guidance_ja`へ日本語で保存する
- 同一入力の再実行では`publication_decision.json`を書き換えない

## O-12 Apply Feedbackの実行

O-12はO-11で明示された今回限りの修正要求だけを、指定されたDraftブロックへ反映する。自由文から対象を推測せず、新しい調査や根拠追加は行わない。

```powershell
rye run python -m note.knowledge_harness.apply_feedback `
  --decision-file _notes/knowledge_harness/decisions/run-20260811-002/publication_decision.json `
  --draft-file _notes/knowledge_harness/drafts/run-20260811-002/draft.rst `
  --manifest-file _notes/knowledge_harness/drafts/run-20260811-002/draft_manifest.json `
  --proposal-file feedback-proposal.json
```

`feedback-proposal.json`はPublication Decisionの指示・対象をそのまま指定し、変更するブロックだけを列挙する。

```json
{
  "instruction_ja": "冒頭を簡潔にしてください。",
  "target_ja": "冒頭段落",
  "changes": [
    {
      "block_id": "block-001",
      "body_rst": "要点を簡潔に示す冒頭です。",
      "packet_refs": ["topics/topic-001/items/item-001"]
    }
  ]
}
```

既定では次の成果物を保存する。

- `_notes/knowledge_harness/revisions/<run_id>/revised_draft.rst`
- `_notes/knowledge_harness/revisions/<run_id>/revision_manifest.json`

検証と生成の規則は次のとおり。

- 同じ`run_id`の`REVISION / ADVANCE`、正常なO-08初稿またはO-12改稿だけを受け付ける
- DraftのSHA-256、今回限りの適用範囲、修正指示、対象、GitHub参照を照合する
- 修正文案に明示された既存`block_id`だけを変更し、本文をDraft内で一意に特定する
- 未指定ブロックと既存Packet参照は変更せず、新しい節、主張、根拠、危険なdirectiveを追加しない
- 変更ごとに修正前後SHA-256、指示、対象、Packet参照、GitHub参照を保存する
- AI修正は同一記事2回までとし、3回目は実行せず`HOLD / HOLD`とする
- 正常時は`REVISED / ADVANCE`と「修正しました。再検証します」を保存し、O-09へ戻す
- O-09はO-08の`DRAFT_READY`とO-12の`REVISED`を同じ検査基準で再検証する
- 同一入力の再実行ではRevised Draftとrevision manifestを書き換えない
- O-12は公開候補への再配置、GitHub操作、公開承認、恒久方針採用を行わない
