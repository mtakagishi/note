*****************************************************
Kubernetes公式に掲載されている事例を体験する
*****************************************************
Last Updated on 2021-04-17

.. |date| date::


`Redisを使用したPHPのゲストブックアプリケーションのデプロイ <https://kubernetes.io/ja/docs/tutorials/stateless-application/guestbook/>`_ について体験メモ

準備
===============
minikubeクラスタ立上げ::

  minikube start
  minikube dashboard

Redisマスター起動
=======================================
マニフェストファイルの確認
----------------------------------------

| デプロイという作業で、k8sはpodの状態を監視して、いい感じに状態維持する。
| さて、今回の事例は、突然、以下のようなyamlが登場。

application/guestbook/redis-master-deployment.yaml::

  apiVersion: apps/v1 # for versions before 1.9.0 use apps/v1beta2
  kind: Deployment
  metadata:
    name: redis-master
    labels:
      app: redis
  spec:
    selector:
      matchLabels:
        app: redis
        role: master
        tier: backend
    replicas: 1
    template:
      metadata:
        labels:
          app: redis
          role: master
          tier: backend
      spec:
        containers:
        - name: master
          image: k8s.gcr.io/redis:e2e  # or just image: redis
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
          ports:
          - containerPort: 6379

体感として、多くのセミナーや講習を受けると、このようなyamlファイルありきで物事が進んでしまい、本質が理解できないまま「こういうものなんだ」「よくわからないけど動いた」という状況になってる気がする。

minikubeのチュートリアルだけを体験したような状態だと、若干混乱するので、少し整理しておく。

マニフェスト
--------------------
k8sのデプロイは動作指針に従って、状態を維持しようとする。この指針をマニフェストと呼ぶみたい。

minikubeチュートリアルでは、 :kbd:`kubectl create deployment hello-node --image=k8s.gcr.io/echoserver:1.4` とだけ叩いた。これは、コンテナイメージである :kbd:`k8s.gcr.io/echoserver:1.4` が動作してればいいというだけの動かし方。

マニフェストは膨大なオプションがあって、yamlファイルにまとめてファイル指定でデプロイ可能。このyamlを「マニフェストファイル」と呼ぶ。

minikubeチュートリアルでいう、 :kbd:`kubectl create deployment hello-node` は :kbd:`kind: Deployment` と :kbd:`name: redis-master`  に対応していて、  :kbd:`--image=k8s.gcr.io/echoserver:1.4` の部分は、 :kbd:`image: k8s.gcr.io/redis:e2e`  という1行に対応されてる。ご覧の通り、他に膨大なオプションを指定したいので、ファイルにまとまっているのだが。特に解説もなくやったらできちゃうので、解釈と理解が飛躍してしまう。

個人的理解は、docker run に対して docker-compose.yaml にまとめたのと同じ関係性。docker run とか体験せずに、初めからdocker-composeから始めると、コンテナのクセみたいのがわからないことになりがちなのと似ている。

結局、minikubeチュートリアルでは下記の色が付いたところだけを指定し、それ以外はデフォルト指定で起動したという解釈。

.. code-block:: yaml
  :caption: application/guestbook/redis-master-deployment.yaml
  :linenos:
  :emphasize-lines: 2,4,23

  apiVersion: apps/v1 # for versions before 1.9.0 use apps/v1beta2
  kind: Deployment
  metadata:
    name: redis-master
    labels:
      app: redis
  spec:
    selector:
      matchLabels:
        app: redis
        role: master
        tier: backend
    replicas: 1
    template:
      metadata:
        labels:
          app: redis
          role: master
          tier: backend
      spec:
        containers:
        - name: master
          image: k8s.gcr.io/redis:e2e  # or just image: redis
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
          ports:
          - containerPort: 6379

マニフェストファイル指定してデプロイする
------------------------------------------------------

実行コマンド、マニフェストファイル指定の場合は、 :kbd:`kubectl apply -f <yamlファイル>` となる。 :kbd:`kind:` 句があるので デプロイもサービスも同じ。 ::

  PS C:\> kubectl apply -f https://k8s.io/examples/application/guestbook/redis-master-deployment.yaml
  deployment.apps/redis-master created

確認コマンド::

  PS C:\> kubectl get pods
  NAME                           READY   STATUS    RESTARTS   AGE
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          2m40s

radisの標準出力の状況確認::

  PS C:\> kubectl logs -f redis-master-f46ff57fd-pp4j9
                  _._
            _.-``__ ''-._
        _.-``    `.  `_.  ''-._           Redis 2.8.19 (00000000/0) 64 bit
    .-`` .-```.  ```\/    _.,_ ''-._
  (    '      ,       .-`  | `,    )     Running in stand alone mode
  |`-._`-...-` __...-.``-._|'` _.-'|     Port: 6379
  |    `-._   `._    /     _.-'    |     PID: 1
    `-._    `-._  `-./  _.-'    _.-'
  |`-._`-._    `-.__.-'    _.-'_.-'|
  |    `-._`-._        _.-'_.-'    |           http://redis.io
    `-._    `-._`-.__.-'_.-'    _.-'
  |`-._`-._    `-.__.-'    _.-'_.-'|
  |    `-._`-._        _.-'_.-'    |
    `-._    `-._`-.__.-'_.-'    _.-'
        `-._    `-.__.-'    _.-'
            `-._        _.-'
                `-.__.-'

  [1] 29 Nov 03:47:56.445 # Server started, Redis version 2.8.19
  [1] 29 Nov 03:47:56.445 # WARNING you have Transparent Huge Pages (THP) support enabled in your kernel. This will create latency and memory usage issues with Redis. To fix this issue run the command 'echo never > /sys/kernel/mm/transparent_hugepage/enabled' as root, and add it to your /etc/rc.local in order to retain the setting after a reboot. Redis must be restarted after THP is disabled.
  [1] 29 Nov 03:47:56.445 # WARNING: The TCP backlog setting of 511 cannot be enforced because /proc/sys/net/core/somaxconn is set to the lower value of 128.
  [1] 29 Nov 03:47:56.445 * The server is now ready to accept connections on port 6379

.. note:: pods名は環境に合わせて読み替えてください。


.. tip:: Ctrl + C で抜けました。

サービス
------------------------------------------------------

minikube では、 :kbd:`kubectl expose deployment hello-node --type=LoadBalancer --port=8080` という感じでpodを外部公開した。指定したのは、サービス名称、タイプ、ポートの三つ。さて、今回は以下のようなマニフェストで作成するらしい。

対応を確認したいので、色と付けてみます。Type指定はないですね。通常は、specの属性に書かれるようです。radisはpod内部から参照できれば良く、デフォルト :kbd:`ClusterIP` タイプとなります。


.. code-block:: yaml
  :caption: application/guestbook/redis-master-service.yaml
  :linenos:
  :emphasize-lines: 2,4,11

  apiVersion: v1
  kind: Service
  metadata:
    name: redis-master
    labels:
      app: redis
      role: master
      tier: backend
  spec:
    ports:
    - port: 6379
      targetPort: 6379
    selector:
      app: redis
      role: master
      tier: backend


構築前確認::

  PS C:\> kubectl get service
  NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
  kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   42m

マニフェストファイル指定してサービスを構築。 :kbd:`kubectl apply -f <yamlファイル>` ::

  PS C:\> kubectl apply -f https://k8s.io/examples/application/guestbook/redis-master-service.yaml
  service/redis-master created

構築後確認::

  PS C:\> kubectl get service
  NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
  kubernetes     ClusterIP   10.96.0.1       <none>        443/TCP    70m
  redis-master   ClusterIP   10.111.45.167   <none>        6379/TCP   6s

ルーティングに関する備考
--------------------------------

.. note:: DeploymentとServiceで、同じラベル付きで作成します。これでPod内のルーティングがうまくいくそうです。


.. code-block:: yaml
  :caption: application/guestbook/redis-master-deployment.yaml
  :linenos:
  :emphasize-lines: 6

  apiVersion: apps/v1 # for versions before 1.9.0 use apps/v1beta2
  kind: Deployment
  metadata:
    name: redis-master
    labels:
      app: redis
  spec:
    selector:
      matchLabels:
        app: redis
        role: master
        tier: backend
    replicas: 1
    template: ...

.. code-block:: yaml
  :caption: application/guestbook/redis-master-service.yaml
  :linenos:
  :emphasize-lines: 6

  apiVersion: v1
  kind: Service
  metadata:
    name: redis-master
    labels:
      app: redis
      role: master
      tier: backend
  spec: ...

Redisスレーブ起動
=======================================

Redisスレーブのデプロイ
-----------------------------------

マニフェストファイルは以下。マスタのマニフェストと比較して異なるところに色を付けました。

13行目は注目。 :kbd:`replicas: 2` なのでスレーブはコンテナ2台となります。

ポートの行は色を付けましたが「マスターと同じポート」です。「同じ指定」ということで、着目の色付けです。

.. code-block:: yaml
  :caption: application/guestbook/redis-slave-deployment.yaml
  :linenos:
  :emphasize-lines: 4,11,13,18,22,23,40

  apiVersion: apps/v1 # for versions before 1.9.0 use apps/v1beta2
  kind: Deployment
  metadata:
    name: redis-slave
    labels:
      app: redis
  spec:
    selector:
      matchLabels:
        app: redis
        role: slave
        tier: backend
    replicas: 2
    template:
      metadata:
        labels:
          app: redis
          role: slave
          tier: backend
      spec:
        containers:
        - name: slave
          image: gcr.io/google_samples/gb-redisslave:v3
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
          env:
          - name: GET_HOSTS_FROM
            value: dns
            # Using `GET_HOSTS_FROM=dns` requires your cluster to
            # provide a dns service. As of Kubernetes 1.3, DNS is a built-in
            # service launched automatically. However, if the cluster you are using
            # does not have a built-in DNS service, you can instead
            # access an environment variable to find the master
            # service's host. To do so, comment out the 'value: dns' line above, and
            # uncomment the line below:
            # value: env
          ports:
          - containerPort: 6379

では実行していきます。実行前::

  PS C:\> kubectl get pod
  NAME                           READY   STATUS    RESTARTS   AGE
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          73m

実行::

  PS C:\> kubectl apply -f https://k8s.io/examples/application/guestbook/redis-slave-deployment.yaml
  deployment.apps/redis-slave created


実行後の確認。二つのコンテナーが増えてます::

  PS C:\> kubectl get pod
  NAME                           READY   STATUS    RESTARTS   AGE
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          77m
  redis-slave-bbc7f655d-7wj2g    1/1     Running   0          3m26s
  redis-slave-bbc7f655d-db6jk    1/1     Running   0          3m26s

スレーブのService
-------------------------

スレーブのServiceマニフェストファイル。注目は12行目。マスターのServiceマニフェストには :kbd:`targetPort: 6379` という記述がありました。今回はないです。ここは後で考えることにして、一旦作成してしまいます。

.. code-block:: yaml
  :caption: application/guestbook/redis-slave-service.yaml
  :linenos:
  :emphasize-lines: 12
  
  apiVersion: v1
  kind: Service
  metadata:
    name: redis-slave
    labels:
      app: redis
      role: slave
      tier: backend
  spec:
    ports:
    - port: 6379

    selector:
      app: redis
      role: slave
      tier: backend

作成前の確認::

  PS C:\> kubectl get services
  NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
  kubernetes     ClusterIP   10.96.0.1       <none>        443/TCP    5h39m
  redis-master   ClusterIP   10.111.45.167   <none>        6379/TCP   4h28m

作成コマンド実行::

  PS C:\> kubectl apply -f https://k8s.io/examples/application/guestbook/redis-slave-service.yaml
  service/redis-slave created

作成後の確認::

  PS C:\> kubectl get services
  NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
  kubernetes     ClusterIP   10.96.0.1       <none>        443/TCP    5h39m
  redis-master   ClusterIP   10.111.45.167   <none>        6379/TCP   4h28m
  redis-slave    ClusterIP   10.100.106.77   <none>        6379/TCP   7s

Port関連
-----------------
Portについては、以下の3つの表現が登場する。詳細はいつか勉強することにしてキーワードだけ抑えておく
:port:VIP、ClusterIPで受け付けるPort
:targetPort:コンテナのPort
:nordPort:ノードIPでのPort

PHPアプリの起動
==========================

.. code-block:: yaml
  :caption: application/guestbook/frontend-deployment.yaml
  :linenos:

  apiVersion: apps/v1 # for versions before 1.9.0 use apps/v1beta2
  kind: Deployment
  metadata:
    name: frontend
    labels:
      app: guestbook
  spec:
    selector:
      matchLabels:
        app: guestbook
        tier: frontend
    replicas: 3
    template:
      metadata:
        labels:
          app: guestbook
          tier: frontend
      spec:
        containers:
        - name: php-redis
          image: gcr.io/google-samples/gb-frontend:v4
          resources:
            requests:
              cpu: 100m
              memory: 100Mi
          env:
          - name: GET_HOSTS_FROM
            value: dns
            # Using `GET_HOSTS_FROM=dns` requires your cluster to
            # provide a dns service. As of Kubernetes 1.3, DNS is a built-in
            # service launched automatically. However, if the cluster you are using
            # does not have a built-in DNS service, you can instead
            # access an environment variable to find the master
            # service's host. To do so, comment out the 'value: dns' line above, and
            # uncomment the line below:
            # value: env
          ports:
          - containerPort: 80

事前確認::

  PS C:\> kubectl get pods
  NAME                           READY   STATUS    RESTARTS   AGE
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          7h26m
  redis-slave-bbc7f655d-7wj2g    1/1     Running   0          6h12m
  redis-slave-bbc7f655d-db6jk    1/1     Running   0          6h12m

作成実行::

  PS C:\> kubectl apply -f https://k8s.io/examples/application/guestbook/frontend-deployment.yaml
  deployment.apps/frontend created

実行直後::

  PS C:\> kubectl get pods
  NAME                           READY   STATUS              RESTARTS   AGE
  frontend-6c6d6dfd4d-hrh8m      0/1     ContainerCreating   0          10s
  frontend-6c6d6dfd4d-sj9sc      0/1     ContainerCreating   0          10s
  frontend-6c6d6dfd4d-spwkg      0/1     ContainerCreating   0          10s
  redis-master-f46ff57fd-pp4j9   1/1     Running             0          7h27m
  redis-slave-bbc7f655d-7wj2g    1/1     Running             0          6h12m
  redis-slave-bbc7f655d-db6jk    1/1     Running             0          6h12m

Runningまで確認、以下のようなオプション指定でも確認できる::

  PS C:\> kubectl get pods -l app=guestbook -l tier=frontend
  NAME                        READY   STATUS    RESTARTS   AGE
  frontend-6c6d6dfd4d-hrh8m   1/1     Running   0          42s
  frontend-6c6d6dfd4d-sj9sc   1/1     Running   0          42s
  frontend-6c6d6dfd4d-spwkg   1/1     Running   0          42s

フロントエンドのServiceを作成
--------------------------------
タイプがnordPortです。LoadBalancerで作成しても良いみたい。

.. code-block:: yaml
  :caption: application/guestbook/frontend-service.yaml
  :linenos:
  :emphasize-lines: 10

  apiVersion: v1
  kind: Service
  metadata:
    name: frontend
    labels:
      app: guestbook
      tier: frontend
  spec:
    # comment or delete the following line if you want to use a LoadBalancer
    type: NodePort 
    # if your cluster supports it, uncomment the following to automatically create
    # an external load-balanced IP for the frontend service.
    # type: LoadBalancer
    ports:
    - port: 80
    selector:
      app: guestbook
      tier: frontend

事前::

  PS C:\> kubectl get services
  NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
  kubernetes     ClusterIP   10.96.0.1       <none>        443/TCP    8h
  redis-master   ClusterIP   10.111.45.167   <none>        6379/TCP   6h51m
  redis-slave    ClusterIP   10.100.106.77   <none>        6379/TCP   143m

実行::

  PS C:\> kubectl apply -f https://k8s.io/examples/application/guestbook/frontend-service.yaml
  service/frontend created


実行後::

  PS C:\> kubectl get services
  NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
  frontend       NodePort    10.108.20.146   <none>        80:31110/TCP   6s
  kubernetes     ClusterIP   10.96.0.1       <none>        443/TCP        8h
  redis-master   ClusterIP   10.111.45.167   <none>        6379/TCP       6h52m
  redis-slave    ClusterIP   10.100.106.77   <none>        6379/TCP       143m

フロントエンドの表示
==================================================

URL特定
-------------------
NordPortタイプの場合::

  minikube service frontend --url

こんな感じ::

  PS C:\> minikube service frontend --url
  * Starting tunnel for service frontend.
  |-----------|----------|-------------|------------------------|
  | NAMESPACE |   NAME   | TARGET PORT |          URL           |
  |-----------|----------|-------------|------------------------|
  | default   | frontend |             | http://127.0.0.1:53377 |
  |-----------|----------|-------------|------------------------|

LoadBalancerの場合::

  kubectl get service frontend

次のような感じでEXTERNAL-IPが確認できるらしい。minikubeでは確認できない。::

  NAME       TYPE        CLUSTER-IP      EXTERNAL-IP        PORT(S)        AGE
  frontend   ClusterIP   10.51.242.136   109.197.92.229     80:32372/TCP   1m


アクセスしてみるとこんな感じです

.. figure:: /ex/kubernetes/Gestbook.png

フロントエンドをスケールする
====================================

実行前::

  PS C:\> kubectl get pods
  NAME                           READY   STATUS    RESTARTS   AGE
  frontend-6c6d6dfd4d-hrh8m      1/1     Running   0          67m
  frontend-6c6d6dfd4d-sj9sc      1/1     Running   0          67m
  frontend-6c6d6dfd4d-spwkg      1/1     Running   0          67m
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          8h
  redis-slave-bbc7f655d-7wj2g    1/1     Running   0          7h20m
  redis-slave-bbc7f655d-db6jk    1/1     Running   0          7h20m

実行、サーバ数を 3 から 5 へ

  PS C:\> kubectl scale deployment frontend --replicas=5
  deployment.apps/frontend scaled

  PS C:\> kubectl get pods
  NAME                           READY   STATUS    RESTARTS   AGE
  frontend-6c6d6dfd4d-hrh8m      1/1     Running   0          68m
  frontend-6c6d6dfd4d-k6b2r      1/1     Running   0          8s
  frontend-6c6d6dfd4d-kwt5q      1/1     Running   0          8s
  frontend-6c6d6dfd4d-sj9sc      1/1     Running   0          68m
  frontend-6c6d6dfd4d-spwkg      1/1     Running   0          68m
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          8h
  redis-slave-bbc7f655d-7wj2g    1/1     Running   0          7h20m
  redis-slave-bbc7f655d-db6jk    1/1     Running   0          7h20m

実行、サーバ数を 5 から 2 へ

  PS C:\> kubectl scale deployment frontend --replicas=2
  deployment.apps/frontend scaled
  PS C:\> kubectl get pods
  NAME                           READY   STATUS    RESTARTS   AGE
  frontend-6c6d6dfd4d-sj9sc      1/1     Running   0          72m
  frontend-6c6d6dfd4d-spwkg      1/1     Running   0          72m
  redis-master-f46ff57fd-pp4j9   1/1     Running   0          8h
  redis-slave-bbc7f655d-7wj2g    1/1     Running   0          7h25m
  redis-slave-bbc7f655d-db6jk    1/1     Running   0          7h25m

クリーンアップ
==============================
* DeploymentとServiceを削除すると、実行中のPodも削除
* ラベルを使用すると、複数のリソースを1つのコマンドで削除

コマンド::

  kubectl delete deployment -l app=redis
  kubectl delete service -l app=redis
  kubectl delete deployment -l app=guestbook
  kubectl delete service -l app=guestbook

確認::

  PS C:\> kubectl get pods
  No resources found in default namespace.

  