
*************************************
サンプルチャートを体験する
*************************************

helm 公式ドキュメントの `クイックスタートガイド <https://helm.sh/ja/docs/intro/quickstart/>`_  を体験

minikubeを立上げて置く
=============================

minikube立上げ::

  minikube start
  minikube dashboard

これで、クラスタ上の動きとの関連も合わせて見ながら体験してみます。

リポジトリ初期化
=============================

リポジトリ初期化::

  helm repo add stable https://charts.helm.sh/stable

検索してみる
=============================

検索してみる::

  helm search repo stable

最新化
=============================

最新化::

  helm repo update

hemlを使ったインストール
===============================

実行前::

  PS C:\> kubectl get pod
  No resources found in default namespace.

サンプルチャートインストール::

  helm install stable/mysql --generate-name
  WARNING: This chart is deprecated
  NAME: mysql-1606825223
  LAST DEPLOYED: Tue Dec  1 21:20:25 2020
  NAMESPACE: default
  STATUS: deployed
  REVISION: 1
  NOTES:
  MySQL can be accessed via port 3306 on the following DNS name from within your cluster:
  mysql-1606825223.default.svc.cluster.local

  To get your root password run:

      MYSQL_ROOT_PASSWORD=$(kubectl get secret --namespace default mysql-1606825223 -o jsonpath="{.data.mysql-root-password}" | base64 --decode; echo)

  To connect to your database:

  1. Run an Ubuntu pod that you can use as a client:

      kubectl run -i --tty ubuntu --image=ubuntu:16.04 --restart=Never -- bash -il

  2. Install the mysql client:

      $ apt-get update && apt-get install mysql-client -y

  3. Connect using the mysql cli, then provide your password:
      $ mysql -h mysql-1606825223 -p

  To connect to your database directly from outside the K8s cluster:
      MYSQL_HOST=127.0.0.1
      MYSQL_PORT=3306

      # Execute the following command to route the connection:
      kubectl port-forward svc/mysql-1606825223 3306

      mysql -h ${MYSQL_HOST} -P${MYSQL_PORT} -u root -p${MYSQL_ROOT_PASSWORD}

実行後::

  PS C:\> kubectl get pod
  NAME                                READY   STATUS    RESTARTS   AGE
  mysql-1606825223-75b4945cdd-gzng2   0/1     Running   0          4s

Podが立ち上がった。Dashboardでも確認

.. figure:: /ex/helm/sample.png


インストールされているhelmチャートの確認
==================================================

確認する ::

  PS C:\> helm ls
  NAME                    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
  mysql-1606825223        default         1               2020-12-01 21:20:25.4443406 +0900 JST   deployed        mysql-1.6.9     5.7.30

リリースをアンインストール
=============================

アンインストール::

  PS C:\> helm uninstall mysql-1606825223
  release "mysql-1606825223" uninstalled

  PS C:\> kubectl get pod
  No resources found in default namespace.

Podがいなくなってます。

minikube終了
=======================

終わったのでminikube止めておきました::

  minikube stop
