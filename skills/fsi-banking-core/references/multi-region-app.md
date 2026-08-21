# マルチリージョン対応 マイクロサービス サンプルアプリケーションの解説

勘定系ワークロードの CDK サンプルには、マルチリージョン環境で稼働するマイクロサービスとして実装されたサンプルアプリケーションが同梱されている。ソースは `assets/sample-cdk/sample-multi-region-app/` に格納されている。

## サンプルアプリケーションの特徴

本サンプルアプリケーションは、マルチリージョン環境で稼働するマイクロサービスとして実装されたアプリケーションである。以下の勘定系機能を提供する。

- 残高参照
- 口座預入れ
- 口座引落し

アプリケーションは下記の 4 つのマイクロサービス（ECS コンテナ）から構成され、**Saga パターン**による補償トランザクションの仕組みを実装することで、分散環境でのトランザクションの整合性を保持するように実装されている。

| サービス名 | 機能 | データベース接続 |
| --- | --- | --- |
| transaction | トランザクション全体を制御するマイクロサービス | DynamoDB（分散トランザクション管理） |
| balance | 口座データに対して引落し/預入れ処理を行うマイクロサービス | Aurora（PostgreSQL または DSQL） |
| count | 口座からの引落し処理の回数を管理するマイクロサービス | Aurora（PostgreSQL または DSQL） |
| worker | 仕掛かり中でペンディング状態となっているトランザクションを処理する常駐サービス | DynamoDB + HTTP API（balance/count） |

基本的には同一のアプリケーションが東京リージョンと大阪リージョンにデプロイされるが、競合状態になることを避けるため、**トランザクションワーカーは東京リージョンのみで稼働**する。（Aurora PostgreSQL 前提の記載だが、Aurora DSQL の場合もデータベースの役割やシーケンスは同様である。）

アーキテクチャ図・預入れ処理のシーケンス図・引落し処理のシーケンス図は、同梱の `assets/sample-cdk/sample-multi-region-app/imgs/` 配下（`architecture.png`、`deposit-sequence.png`、`withdraw-sequence.png` など）を参照。

## API エンドポイント

### Transaction Service

- `POST /transaction/deposit` - 預入れトランザクション開始
- `POST /transaction/withdraw` - 引落しトランザクション開始
- `GET /transaction/{transactionId}` - トランザクション状態照会

### Balance Service

- `GET /balance` - 残高照会
- `PUT /balance/withdraw` - 引落し処理
- `PUT /balance/cancel_withdraw` - 引落しキャンセル（補償トランザクション）
- `PUT /balance/deposit` - 預入れ処理
- `PUT /balance/cancel_deposit` - 預入れキャンセル（補償トランザクション）
- `GET /health` - ヘルスチェック

### Count Service

- `PUT /count/withdraw` - 引落し回数増加
- `PUT /count/cancel_withdraw` - 引落し回数キャンセル（補償トランザクション）
- `GET /health` - ヘルスチェック

**ビジネスロジック**: 引落し回数が 3 回を超えると手数料 100 円が追加される。

## デプロイ

デプロイ手順の概要は「[デプロイ手順 [勘定系]](./deployment.md)」の手順 5 を参照。詳細な手順は同梱の `assets/sample-cdk/sample-multi-region-app/deploy.md` に格納されている。ECS コンテナアプリケーションおよび Aurora DB のセットアップが必要である。

なお、同梱ソースには自動フェイルオーバー・スイッチオーバーの動作確認用ドキュメント（`auto-failover-sample-application.md`、`failover-sample-application.md`）や、負荷試験クライアント（`client/locustfile.py` による Locust ベースのクライアント）も含まれる。
