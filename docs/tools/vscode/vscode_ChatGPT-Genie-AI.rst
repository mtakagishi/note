.. _ChatGPT-Genie-AI:

Genie AIを使った VSCode上でのChatGPT連携
==========================================

「ChatGPT - Genie AI」は、Visual Studio Code (VSCode) を拡張してChatGPTと連動できるようにします。コーディング中のChatGPTとの連携を効率化できます。

要件
------

OpenAIのAPI Keyが必要です。

インストール方法
------------------

まず、VSCodeの拡張機能マーケットプレイスから「ChatGPT - Genie AI」を検索し、インストールしてください。

使用方法
----------

1. **Genie AIを開く**: VSCodeのサイドバーの魔法のランプを押すとジーニーの登場です。

2. **質問の投稿**: Genie AIのパネルの入力欄に、質問やコードを入力して送信してください。

3. **AIによる回答**: 質問を送信すると、AIが適切なコードや情報を提案してくれます。提案されたコードはチャット欄にある ``Copy`` ボタンでクリップボードにコピーしたり、``Insert`` ボタン でカーソル位置にそのまま挿入することができます。

4. **インラインでの使用**: エディタ内の内容を元に直接質問できます。内容を選択して右クリックで質問を選択してください。

初期設定の質問
--------------

- **Add tests** : 選択したコードからテストコードを生成します。 ＝ ``Implement tests for the following code`` 
* ``Find bugs``: 選択したコードの問題点を探します。＝ ``Find problems with the following code``

- **Optimize** : 初期値は``Optimize the following code`` 選択したコードの最適化を提案します。

- **Explain**  : 選択したコードの内容を説明します。＝ ``Explain the following code``
- **Add comments** : 選択したコードにコメントを追加してくれます。＝ ``Add comments for the following code``
- **Complete code** : 選択したコードを完成させます。＝ ``Complete the following code``
- **Ad-hoc prompt** : 選択した内容に対してアドホックにAIに要求するための入力プロンプトが表示されます。

初期設定は英文で設定されてます。質問内容は ``Settings`` で変更可能です。必要に応じて母国語の質問文に変更してください。

.. rubric:: 参考URL

https://github.com/ai-genie/chatgpt-vscode
