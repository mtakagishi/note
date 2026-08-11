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
