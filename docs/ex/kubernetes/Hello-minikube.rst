個人端末でKubernetesに慣れる
==============================================
Last Updated on 2021-04-17

.. |date| date::

minikubeを動かす
--------------------------------------
kubernetesはクラスタという単位で管理する。minikubeは、個人パソコンになんちゃってクラスタを作れる。

まずは、docker desktop のsettgingから、「Enable Kubernetes」をonにする。

.. figure:: /ex/kubernetes/enable_k8s.png

続いて状況コマンド :kbd:`minikube states` ::

  PS C:\> minikube status
  * Profile "minikube" not found. Run "minikube profile list" to view all profiles.
    - To start a cluster, run: "minikube start"

指示通り :kbd:`minikube start`　でクラスタを作る。クラスタはコンテナが動く箱み。::

  PS C:\> minikube start
  * Microsoft Windows 10 Pro 10.0.18363 Build 18363 上の minikube v1.15.1
  * dockerドライバーが自動的に選択されました
  * コントロールプレーンのノード minikube を minikube 上で起動しています
  * Pulling base image ...
  * Kubernetes v1.19.4 のダウンロードの準備をしています
      > preloaded-images-k8s-v6-v1.19.4-docker-overlay2-amd64.tar.lz4: 486.35 MiB
  * docker container (CPUs=2, Memory=1991MB) を作成しています...
  * Docker 19.03.13 で Kubernetes v1.19.4 を準備しています...
  * Kubernetes コンポーネントを検証しています...
  * 有効なアドオン: storage-provisioner, default-storageclass
  * Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default

再度確認::

  PS C:\> minikube status
  minikube
  type: Control Plane
  host: Running
  kubelet: Running
  apiserver: Running
  kubeconfig: Configured

良い感じ。 :kbd:`minikube dashboard` を打ち込んでGUIでも確認する。::

  PS C:\> minikube dashboard
  * ダッシュボードを有効化しています...
  * ダッシュボードの状態を確認しています...
  * プロキシを起動しています...
  * プロキシの状態を確認しています...
  * Opening http://127.0.0.1:63120/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/ in your default browser...

.. figure:: /ex/kubernetes/k8s_dashboard.png

   

コンテナを動かしてみる
--------------------------------
`チュートリアル <https://kubernetes.io/ja/docs/tutorials/hello-minikube/>`_ に従って叩いてみる。::

  PS C:\> kubectl create deployment hello-node --image=k8s.gcr.io/echoserver:1.4
  deployment.apps/hello-node created

あっけないほど一瞬で終わる。

デプロイをダッシュボード確認
-------------------------------------------
ダッシュボード見ると「ワークロードの状態」が変化している

.. image:: /ex/kubernetes/k8s_dashboard_hello-node.png


デプロイをコマンドでの確認
-------------------------------------------

:kubectl get deployments: Deploymentの確認。Deploymentは、Podを監視し状態維持に努める
:kubectl get pods: Podの確認。Podはコンテナのグループ
:kubectl get events: ログみたいな感じ。k8sが実行した内容の履歴が見れる
:kubectl config view: 設定状況を確認できる

Podの公開する
--------------------------
Podを外部からアクセス可能にする。::

  PS C:\> kubectl expose deployment hello-node --type=LoadBalancer --port=8080
  service/hello-node exposed

コマンドで確認する::

  PS C:\> kubectl get services
  NAME         TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
  hello-node   LoadBalancer   10.97.240.161   <pending>     8080:30289/TCP   110s
  kubernetes   ClusterIP      10.96.0.1       <none>        443/TCP          104m

.. hint:: EXTERNAL-IPが<pending>になっているが、実際のサービスの場合、Serviceにアクセスするための外部IPアドレスが提供される。

minikubeの場合は :kbd:`minikube service <service>`  で接続確認。::

  PS C:\> minikube service hello-node
  |-----------|------------|-------------|---------------------------|
  | NAMESPACE |    NAME    | TARGET PORT |            URL            |
  |-----------|------------|-------------|---------------------------|
  | default   | hello-node |        8080 | http://192.168.49.2:30289 |
  |-----------|------------|-------------|---------------------------|
  * Starting tunnel for service hello-node.
  |-----------|------------|-------------|------------------------|
  | NAMESPACE |    NAME    | TARGET PORT |          URL           |
  |-----------|------------|-------------|------------------------|
  | default   | hello-node |             | http://127.0.0.1:63811 |
  |-----------|------------|-------------|------------------------|

.. image:: /ex/kubernetes/brows_hello-node.png

k8s.gcr.io　というコンテナイメージは、httpリクエストに対して基本的な情報を応答してくれるんですね。ということは、自前のアプリをコンテナ化できれば同じことができるということ。

お掃除
-------------------
ここまでのことを「何事もなかったように掃除」。minikubeの掃除は再利用を考えると不要かもしれない。実践でもリソースの掃除はしてもクラスタは作ったら消すことは少ない。

k8s掃除::

  kubectl delete service hello-node
  kubectl delete deployment hello-node

minikube掃除::

  minikube stop
  minikube delete