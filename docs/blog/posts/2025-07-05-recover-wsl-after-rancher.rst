.. post:: 2025-07-05
   :tags: WSL, Rancher, Windows, Linux環境, トラブルシューティング
   :category: 開発環境
   :author: mtakagishi
   :language: ja

Rancher利用後に壊れたWSL環境を再構築した手順
===============================================

過去に Windows 上で Rancher を導入していた影響で、`wsl install` が正常に動作せず、WSL2 を利用できない状態が続いていた。今回、その WSL 環境を完全に初期化し、再構築することに成功したので、その手順を記録しておく。

背景と問題の発生状況
--------------------

以前、Docker Desktop や Rancher Desktop を導入した経緯があり、WSL の仮想環境に `docker-desktop` や `rancher-desktop` などのディストリビューションが自動で追加されていた。

これらをアンインストールした後も、`wsl install` コマンドがエラーを返すようになり、Ubuntu を含む WSL 環境の導入が一切できない状態に。

原因は、おそらく **WSLの内部状態が壊れていた** ことにある。

解決のためのアプローチ
----------------------

以下の手順で、WSL を一度完全に初期化し、再インストールを行った。

1. **現在の WSL 状態の確認**

   .. code-block:: powershell

      wsl --list --all --verbose

2. **不要なディストリビューションの削除**

   .. code-block:: powershell

      wsl --unregister docker-desktop
      wsl --unregister docker-desktop-data
      wsl --unregister rancher-desktop

3. **WSL 機能を完全に無効化**

   .. code-block:: powershell

      dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart
      dism.exe /online /disable-feature /featurename:VirtualMachinePlatform /norestart

   再起動を実施。

4. **WSL 機能の再有効化**

   .. code-block:: powershell

      dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
      dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

   再び再起動。

5. **WSL の再インストール**

   .. code-block:: powershell

      wsl --install

   これで再び Ubuntu などの WSL ディストリビューションがインストール可能な状態に戻った。

今後の方針と教訓
----------------

- Rancher Desktop や Docker Desktop のアンインストール後でも、WSL 内部に痕跡が残っている場合がある。
- **`wsl --unregister` + `dism` のセットによる初期化が有効** だった。
- 開発マシンで仮想化関連ツールを切り替える場合は、WSL の状態管理にも注意が必要。
- 今後は WSL の破損時に備え、定期的な `wsl --export` によるバックアップも検討したい。

.. rubric :: 記事情報

:著者: mtakagishi
:公開日: 2025-07-05
