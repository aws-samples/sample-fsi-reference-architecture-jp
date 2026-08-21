# リファレンスアーキテクチャ解説 [レジリエンス - モダンアーキテクチャ (オンラインバンキング アプリケーション サンプル)]

## 前提条件

- 本リファレンスアーキテクチャは、レジリエンスの観点でマイクロサービスの価値を例示する目的で作成されたものである。
- 従来から、金融システムに関しては勘定系ワークロードのサンプル（金融ワークロードアーキテクチャ解説 [勘定系]）を提供している。この中では Saga パターンにおける補正トランザクションを発行する、マイクロサービスなどで一般的な整合性担保のデザインパターンを採用している。一方で、マイクロサービスなどの分散システムでのデザインパターンは Saga パターンなど様々あり、本リファレンスアーキテクチャは別のパターンを採用している。
- 本リファレンスアーキテクチャは３つに分けて AWS Cloud Development Kit (AWS CDK) によるサンプルテンプレートとして提供している。このアーキテクチャでは、Amazon DynamoDB をメインデータストアとして、業務ロジックは AWS Lambda、Lambda のトリガーとして API ホストやイベント起動に Amazon API Gateway、Amazon EventBridge、Amazon SQS、フロントエンドのホスティングに Amazon S3、Amazon CloudFront を採用している。
- FISC 安全対策基準 実務基準の対策（`fisc-mapping.md`）では３つのテンプレートのうち、バックエンドシステム (online-banking-app-backend) を前提として記載を整理している。
- 本リファレンスアーキテクチャは Kiro と Amazon Q Developer により開発している。アーキテクチャ図を元に初期版を作成させたのち、Vibe Coding を中心に修正している。それによりプログラムに関しては 2〜3 週間程で開発が可能となった。

## ユースケース

モバイルバンキングアプリケーションを題材として、口座開設、残高照会、振込処理の主要機能を各種業務を取り扱うシステムを想定している。本リファレンスアーキテクチャで示している構成は、高い可用性とスケーラビリティが求められるモダンなマイクロサービスアーキテクチャに基づいており、金融業界に限らず様々な業界のミッションクリティカルなシステムに応用できる汎用的なものとなっている。

本ドキュメントは「リファレンスアーキテクチャの解説」と「金融システムにおけるマイクロサービスアーキテクチャのメリット」の二部構成になっている。マイクロサービスの用語の解説等は後半の「金融システムにおけるマイクロサービスアーキテクチャのメリット」側を確認すること。

## リファレンスアーキテクチャの解説

### アーキテクチャの概要

![アプリケーション全体の概念図](../assets/images/mobile-banking-arch-overview.png)

本リファレンスアーキテクチャでは、以下３つのスタックに分けて実装されている。

- **OnlineBankingAppFrontendStack**: React SPA によるフロントエンド
- **OnlineBankingAppBackendStack**: Lambda + DynamoDB によるマイクロサービス群
- **TemporaryCoreBankingSystemStack**: 勘定系システムの API を擬似的に作成したバンキングシステム

ここではマイクロサービスで構成される **OnlineBankingAppBackendStack** について解説する。フロントエンドの機能、サンプルアプリの使い方に関しては本ドキュメント後半の「アプリケーション利用手順」を参照すること。

### OnlineBankingAppBackendStack

OnlineBankingAppBackendStack は機能単位に Lambda 上に実装されており、データストアは DynamoDB を利用している。フロントエンドからのリクエストは API Gateway のエンドポイントを呼び出す形になっている。

口座開設、振込の２つの処理は非同期処理として利用者からのリクエストを受け付けたのち、状態変更をイベントを変更履歴（監査証跡）として残す[イベントソーシング](#4-c-イベントソーシング)の形で処理する。勘定系 API を呼び出す際の一貫性を担保するため、トランザクションアウトボックスを採用し、Lambda の内部には再実行の仕組みを組み込んでいる。再実行に関しては AWS Well-Architected フレームワーク 信頼性の柱 [REL05-BP03 再試行呼び出しを制御および制限する](https://docs.aws.amazon.com/ja_jp/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html) も参照すること。

#### 提供 API の概要

モバイルバンキング機能

- 口座開設 API (/api/accounts/\*): 口座開設の申込および審査に関連する機能
- 照会サービス API (/api/balance/\*): 口座残高, 取引履歴等データの参照機能
- 振込管理 API (/api/transfer): 振込依頼を受け付ける機能

顧客管理/認証認可

- 認証関連 API (/api/auth/\*): 口座開設後のログインおよび残高照会, 振込等の認可機能
- ユーザー管理 API (/api/users/\*): 口座開設時に受領した顧客情報を管理する機能

銀行管理者機能（アプリ挙動を理解しやすいように最小限実装）

- 管理者 API (/admin/\*): 振込のイベントソーシングの状態遷移を可視化・口座開設の擬似的な承認

#### イベントソーシングをベースにした実装機能の解説

##### 口座開設処理フロー

**実装の解説**

口座開設処理は、イベントソーシングとトランザクションアウトボックスパターンを組み合わせて実装されている。顧客による申込、管理者による承認、システムによる自動処理の 3 段階で構成され、申込情報はイベントストアに永続化され、アウトボックステーブルを経由して外部システムとの連携を行う。処理は非同期で実行され、各ステップの完了後にイベントが発行される仕組みとなっている。

**実装によるメリット**

この設計により、金融システムに求められる厳格な記録管理要件を満たす完全な監査証跡を提供できる。アウトボックスパターンによりデータベース更新とイベント発行の原子性が保証され、システムの整合性を確実に維持する。また、非同期処理アーキテクチャにより外部システム（Core Banking API、認証システム）の障害がフロントエンドに影響せず、優れたユーザー体験を実現できる。外部 API 呼び出し失敗時の自動リトライ機能により信頼性を確保し、イベント駆動設計により、メール通知などの副次的処理を疎結合で実装でき、システム全体の保守性と拡張性が向上する。

**考慮点**

非同期処理による最終的整合性のため、リアルタイムでの状態確認が必要な場合は別途考慮が必要である。また、複数段階の処理における各段階での障害発生時の適切な補償処理の実装と、外部システムとの連携における冪等性の確保が重要となる。

**処理フロー**

```mermaid
sequenceDiagram
    participant Customer as 顧客
    participant Frontend as フロントエンド
    participant API as API Gateway
    participant EventStore as EventStore
    participant Outbox as Outbox Table
    participant EventBridge as EventBridge
    participant Admin as 管理者
    participant Processor as Outbox Processor
    participant CoreBanking as Core Banking
    participant Auth as 認証システム

    Note over Customer, Auth: 1. 口座開設申請フロー
    Customer->>Frontend: 口座開設依頼
    Frontend->>API: POST /api/accounts
    API->>API: 申込ID・トランザクションID生成
    API->>EventStore: 口座開設申請イベント保存
    API->>Outbox: notify_receipt アクション記録
    API->>EventBridge: イベント発行
    API->>Frontend: ステータス PENDING で完了レスポンス

    Note over Admin, EventBridge: 2. 口座開設承認フロー
    Admin->>API: POST /api/accounts/confirm/{transactionId}
    API->>EventStore: 申込情報取得・ステータス CONFIRMED に更新
    API->>Outbox: create_account アクション記録
    API->>EventBridge: イベント発行

    Note over Processor, Auth: 3. 自動処理：口座開設完了フロー
    Outbox->>Processor: DynamoDB Stream トリガー
    Processor->>CoreBanking: 顧客作成（customerId取得）
    Processor->>CoreBanking: 口座作成（accountId, accountNumber取得）
    Processor->>Auth: ユーザー登録（loginId, temporaryPassword取得）
    Processor->>EventStore: 完了イベント記録・ステータス COMPLETED
    Processor->>EventBridge: 完了イベント発行
    Note right of Processor: メール通知（本サンプルでは未実装）
```

**補足**

本構成では EventBridge を採用することで、イベント発行を通じて非同期の並行処理（ファンアウト）を追加実装できるようになっている。これにより、AI による本人確認書類の審査, リスクスコアリング, 人による審査, 顧客への通知などを並列実行するのが容易になる。

##### 振込処理フロー

**実装の解説**

振込処理は、出金と入金を分離したマイクロサービスアーキテクチャで実装されており、イベントソーシング、イベントドリブンアーキテクチャ、トランザクションアウトボックスパターンを組み合わせた設計である。振込リクエストはイベントストアに記録され、EventBridge を通じてイベントドリブンな処理連携を行う。出金・入金の各処理は SQS キューを通じて非同期実行され、DynamoDB Stream をトリガーとするアウトボックスパターンにより外部システムとの整合性を保証する。

**実装によるメリット**

出金と入金を独立したサービスで処理することで障害の局所化を実現し、一方の処理で問題が発生しても他方への影響を最小限に抑える。EventBridge と SQS による非同期処理アーキテクチャにより、高負荷時でもシステム全体のスケーラビリティを確保し、安定したサービス提供を可能にする。デッドレターキューの実装により失敗した処理の自動再試行と詳細な監視を行い、冪等性の確保により重複処理を防止してシステムの信頼性を向上させる。イベントソーシングパターンにより振込処理の全工程にわたる完全な状態追跡が可能となり、金融取引に求められる厳格な監査要件と障害時の原因究明を支援する。

**考慮点**

分散処理による複雑性の増加に伴い、出金完了後の入金処理失敗時の補償処理の実装が重要である。また、残高不足や口座凍結などの事前チェック、ネットワーク障害による処理の重複実行に対する冪等性の確保、処理の進行状況をユーザーに適切に通知するための仕組みや、長時間処理が滞留した場合のアラート機能の実装も考慮が必要である。

```mermaid
sequenceDiagram
    participant Customer as 顧客
    participant Frontend as フロントエンド
    participant API as API Gateway
    participant EventStore as EventStore
    participant EventBridge as EventBridge
    participant WithdrawSQS as Withdraw SQS
    participant DepositSQS as Deposit SQS
    participant WithdrawWorker as Withdraw Worker Lambda
    participant DepositWorker as Deposit Worker Lambda
    participant WithdrawOutbox as Withdraw Outbox Lambda
    participant DepositOutbox as Deposit Outbox Lambda
    participant OutboxTable as Outbox Table
    participant CoreBanking as Core Banking API
    participant MailLambda as Mail Notification Lambda

    Note over Customer, MailLambda: 1. 顧客モード：振込依頼
    Customer->>Frontend: 振込依頼
    Frontend->>API: POST /api/transfers
    API->>API: 事前チェック（口座存在確認・残高確認）
    alt 残高不足時
        API->>Frontend: エラー返却
    else 正常時
        API->>API: トランザクションID生成
        API->>EventStore: TransferRequested イベント保存
        API->>EventBridge: WithdrawRequested イベント発行
        API->>Frontend: ステータス RECEIVED で受付完了レスポンス
    end

    Note over EventBridge, CoreBanking: 2. 自動処理：出金フェーズ
    EventBridge->>WithdrawSQS: WithdrawRequested イベント
    WithdrawSQS->>WithdrawWorker: メッセージ処理
    WithdrawWorker->>OutboxTable: 出金レコード（withdraw-{transactionId}）作成
    WithdrawWorker->>EventStore: ステータス WITHDRAW_REQUESTED に更新
    OutboxTable->>WithdrawOutbox: DynamoDB Stream トリガー
    WithdrawOutbox->>OutboxTable: ステータス processing に更新
    WithdrawOutbox->>CoreBanking: 出金処理実行（リトライ付き）
    WithdrawOutbox->>OutboxTable: ステータス completed に更新
    WithdrawOutbox->>EventBridge: DepositRequested イベント発行

    Note over EventBridge, CoreBanking: 3. 自動処理：入金フェーズ
    EventBridge->>DepositSQS: DepositRequested イベント
    DepositSQS->>DepositWorker: メッセージ処理
    DepositWorker->>OutboxTable: 入金レコード（deposit-{transactionId}）作成
    DepositWorker->>EventStore: ステータス DEPOSIT_REQUESTED に更新
    OutboxTable->>DepositOutbox: DynamoDB Stream トリガー
    DepositOutbox->>OutboxTable: ステータス processing に更新
    DepositOutbox->>CoreBanking: 入金処理実行（リトライ付き）
    DepositOutbox->>OutboxTable: ステータス completed に更新
    DepositOutbox->>EventBridge: TransferCompleted イベント発行

    Note over EventBridge, MailLambda: 4. 自動処理：完了通知
    EventBridge->>MailLambda: TransferCompleted イベント受信
    MailLambda->>CoreBanking: 送金元口座・顧客情報取得
    Note right of MailLambda: 振込完了メール送信<br/>（本サンプルでは未実装）
```

### メール配信基盤に関する注意事項

本リファレンスにおいてはイベント実行する Lambda は準備しているが、実際のメール送信処理は疑似的な実装としてログ出力のみを行っている。

メール配信処理のログ出力：

```typescript
// メール配信処理
console.log(
  '📧 メール配信基盤はこのサンプルアーキテクチャの対象外ですが、このLambdaから呼び出す形を想定して設計しています',
);
console.log('📧 実装時は以下のような外部API呼び出しを行います:', {
  recipient: sourceCustomer.email,
  subject: emailData.subject,
  template: 'transfer-completion',
  transactionId: transactionId,
});
```

### マルチリージョン対応の考慮事項

レジリエンスの観点でマルチリージョン化にあたってのポイントを記載する。

#### アプリケーション配信の観点

本リファレンスアーキテクチャではドメイン取得をせずに展開できるようにカスタムドメインを利用せず、AWS 発行の CloudFront のデフォルトドメインを利用しているため、単一リージョンでの CloudFront Distribution による静的コンテンツ配信（S3 + CloudFront + WAF）にて実装されている。

カスタムドメインが使えない前提のままマルチリージョン構成にする場合は、CloudFront Origin Group を活用したオリジンレベルでの冗長化が有効である。具体的には、プライマリリージョン（ap-northeast-1）とセカンダリリージョン（ap-southeast-1）にそれぞれ S3 バケットを配置し、S3 Cross-Region Replication でコンテンツを同期する。その上で CloudFront Distribution の Origin Group 機能を使用して、プライマリオリジンに障害が発生した際（403, 404, 500, 502, 503, 504 エラー）に自動的にセカンダリオリジンにフェイルオーバーする構成とする。この手法により、カスタムドメインを使用せずとも、単一の CloudFront Distribution でマルチリージョンの可用性を実現できる。API のホスティングに関しても同様に CloudFront を使いオリジンフェイルオーバーにて実現する形になる。

一方、本番システムにおいては独自ドメインを利用する前提となる。Route 53 Application Recovery Controller の利用やフロントエンドの Standby takes over primary (STOP) 手法などにより実装可能である。具体的な方法については [Amazon Route 53 を用いたディザスタリカバリ (DR) のメカニズム](https://aws.amazon.com/jp/blogs/news/creating-disaster-recovery-mechanisms-using-amazon-route-53/) も参照すること。

#### イベント処理の切り替え

口座開設、および振込処理の Lambda はイベントソーシングを前提に実装されているので、イベント情報の履歴を DynamoDB に書き込む設計となっている。DynamoDB Global Tables の強い整合性を有効化することで、各種イベントのステータスがマルチリージョンに同期される。リージョン切り替えに当たって不整合が出たデータに関しては、イベント状況に応じて滞留イベントの再実行を行うことが可能である。

再実行にあたり勘定系システムの API を呼び出す設計となっている機能は、アプリケーション画面上は非同期処理の依頼を受け付けた旨表示の上で、実際には勘定系システムを待って再実行する流れとなる。これにより顧客のアプリケーション体験を損なわない上で実処理を実行することができる。特に口座開設のようなオペレーション上受付と処理、開設に時差のある機能に関しては有効な手法となる。

## 金融システムにおけるマイクロサービスアーキテクチャのメリット

続いて、レジリエンスにおけるマイクロサービスアーキテクチャの利点をおさらいする。

### 1. アーキテクチャ解説における前提

一般的に、マイクロサービスとモノリシックなシステムはしばしば比較され、どちらが優れるか議論される。しかしどちらかが明確に優れるものではなく、双方メリット、デメリットが存在する。故に採用にあたっては組織やシステムの特性がどちらを許容できるかを第一に考えるのを推奨する。このリファレンスアーキテクチャはマイクロサービスをむやみに推奨するものではなく、方法論の例示に主眼をおいてサンプル開発した。上記を前提として、本章では主にマイクロサービスの観点を記載する。

### 2. レジリエンスにおけるマイクロサービスの利点

以下の図、左側で示すように、モノリスでは単一のアプリケーションで障害が発生した場合、システム全体が影響を受けてしまい、一部の機能のみに問題があってもサービス全体が停止するリスクがある。また、負荷が集中した際にはアプリケーション全体をスケールする必要があり、リソースの効率的な利用が困難になる場合がある。

一方、右側で示すようにマイクロサービスでは各サービスが独立して動作するため、一つのサービスで障害が発生しても他のサービスは正常に稼働し続けることができる。これにより障害の影響範囲を局所化でき、システム全体の可用性を向上させることが可能になる。また、負荷の高いサービスのみを個別にスケールアウトできるため、リソースの効率的な活用とコスト最適化を実現できる。

![レジリエンスにおけるモノリスとマイクロサービス比較図](../assets/images/mobile-banking-arch-resilience.png)

これらの利点は何も実行環境に限ったものではなく、アプリケーションの開発・デプロイにおいても同様である。モノリスなシステムは全資源が差し替わるため、作業ミスのリスクなどを避けるため作業を減らすためにリリース日を絞り、資源凍結をおこなったうえで全体のリグレッションテストを行う傾向が強まる。金融機関の多くのシステムはこのような手法を取られている。一方、マイクロサービスに分割し、呼び出されるインターフェイスを定義することで、サービス毎に独立したリグレッション、作業ミスの影響の極小化を行えるため一度のリリース作業の負担を軽減することができる。

### 3. マイクロサービスとモノリシックなシステムの特性の違い

マイクロサービスには従来のアプリケーション設計の課題に対してメリットも多いが、逆に難易度が上がる点もある。その論点でまとめたものが以下の図となる。この図では **結合度**, **柔軟性とアジリティ**, **スケーラビリティ**, **障害の影響範囲**, **アーキテクチャの複雑度**, **データ整合性の担保** を元に記載しているが、従来のモノリスに合わせて設計されたアプリケーションやそれに慣れた開発者の視点では、右下の **アーキテクチャの複雑度**, **データ整合性の担保** に特に課題を感じる人が多いと考える。

![モノリスとマイクロサービスのスペクトラム](../assets/images/mobile-banking-arch-readme-vs-monolice-microservices.png)

この具体例を一つ紹介する。

#### モノリスとマイクロサービスにおける整合性担保の違い

![マイクロサービスにおける整合性/一貫性の課題](../assets/images/mobile-banking-arch-transaction-and-consistency.png)

左側の図に示すように、モノリスでは単一のアプリケーションが単一のデータベースに対してトランザクションを実行する。これにより ACID 特性の活用[^1]、出金元口座の残高更新と振込先口座の残高更新を同一トランザクション内で実行し、どちらかが失敗した場合は全体をロールバックできるシンプルな整合性保証、全ての処理が同期的に実行され、処理完了時点で整合性が保証されるという観点での利点があり、アプリケーションのアーキテクチャ設計をシンプルにする。

一方で、マイクロサービスでは右側の図が示すように、複数の独立したサービスとデータベースが関与する。各サービスが独立したデータベースを持つため、従来の ACID トランザクションが使用できない点。また、サービス間通信でネットワーク障害や部分的な失敗が発生する可能性を考慮する必要がある。これらを加味してなおシステムとしての挙動を担保するには即座に全体の整合性を保証するのではなく、最終的に整合性が取れる設計が必要となる。実現の難易度が高く、アーキテクチャの複雑度が増す。これがマイクロサービスにおける整合性/一貫性の課題である。

[^1] **ACID 特性の活用**: データベースの原子性（Atomicity）、一貫性（Consistency）、独立性（Isolation）、永続性（Durability）

この課題を解決するために、以下のようなデザインパターンが重要になる。

### 4. 分散システムにおけるデザインパターン

マイクロサービスをはじめとする分散システムにおいては、複数のサービス間での整合性保証や障害処理が複雑になるため、これらの課題を解決するための確立されたデザインパターンの採用が重要になる。適切なパターンを選択することで、システムの信頼性と保守性を大幅に向上させることができる。詳細については AWS 規範的ガイダンスの [マイクロサービスにおけるデータ永続化の有効化](https://docs.aws.amazon.com/ja_jp/prescriptive-guidance/latest/modernization-data-persistence/welcome.html) も参照すること。

ここでは、データ永続化において代表的な考え方である、勘定系でも採用される Saga パターン[^2]、および本リファレンスで採用するトランザクションアウトボックスパターン、イベントソーシング、CQRS の概念について簡単に紹介する。

[^2] 勘定系での Saga パターン利用範囲

![勘定系のSagaパターン](../assets/images/mobile-banking-arch-saga-corebanking.png)

#### 4-a. Saga パターン

Saga パターンは、分散システムにおいて複数のサービス間でのトランザクション整合性を保証するためのデザインパターンである。

![Sagaパターンの実装例](../assets/images/mobile-banking-arch-saga-pattern.png)

このパターンでは、各ステップで失敗した場合に前のステップを取り消すための補償トランザクションを定義することで、分散環境でも整合性を保証する。実装方式としては、中央制御型のオーケストレーションと分散制御型のコレオグラフィの 2 つのアプローチがあり、システムの要件に応じて選択できる。金融システムにおいては、例えば振込処理で出金から入金への各ステップにおいて、失敗時の補償処理を実装することで、資金の整合性を確実に保つことができる。

#### 4-b. トランザクションアウトボックスパターン

トランザクションアウトボックスパターンは、データベースの更新とメッセージ送信を原子的に実行するためのパターンである。

![トランザクションアウトボックスの実装例](../assets/images/mobile-banking-arch-transaction-outbox-pattern.png)

このパターンでは、データベース更新とイベント発行を同一トランザクション内で実行することで原子性を保証する。具体的には、発行すべきイベントを一時的に格納するアウトボックステーブルを用意し、別プロセスがこのテーブルを監視してイベントを外部システムに送信する仕組みである。また、イベント ID による重複排除機能により、同じイベントが複数回処理されることを防ぎ、システムの信頼性を確保する。

#### 4-c. イベントソーシング

イベントソーシングは、アプリケーションの状態変更をイベントの連続として記録するパターンである。

![イベントソーシングの例](../assets/images/mobile-banking-arch-event-sourcing.png)

このパターンでは、すべての業務イベントを時系列でイベントストアに永続化し、これらのイベントを順次適用することで現在の状態を復元できる。完全な変更履歴が保持されるため、金融システムに求められる厳格な監査要件を満たすことができ、さらに過去の任意の時点での状態を再現する「時間旅行」機能も実現可能である。また、CQRS パターンとの親和性が高く、イベントストアから読み取り専用ビューを効率的に構築できるため、参照処理のパフォーマンス向上にも寄与する。

#### 4-d. CQRS（Command Query Responsibility Segregation）

CQRS は、コマンド（更新処理）とクエリ（参照処理）の責任を分離するアーキテクチャパターンである。

![CQRSパターンの実装例](../assets/images/mobile-banking-arch-CQRS.png)

このパターンでは、更新用と参照用で異なるデータモデルとデータストアを使用することで読み書きを分離し、それぞれの処理に最適化された設計を実現する。参照処理に特化したデータ構造により高速な検索が可能になり、読み取り負荷と書き込み負荷を独立してスケールできるため、システム全体のスケーラビリティが向上する。特にイベントソーシングと組み合わせることで、イベントストアから読み取り専用ビューを構築し、複雑な集計処理や分析処理を効率的に実行できるアーキテクチャを構築できる。

## バックエンドスタックの実装詳細（CDK ソースより）

`assets/sample-cdk/` の CDK 実装から読み取れる、OnlineBankingAppBackendStack の主要なリソース構成を以下に整理する。

### DynamoDB テーブル

すべてカスタマー管理キー（KMS）で暗号化し、Point-in-Time Recovery を有効化している。

| テーブル | パーティションキー / ソートキー | 用途 | Stream |
| --- | --- | --- | --- |
| UsersTable | userId | ユーザー・認証情報（GSI: CustomerIdIndex, LoginIdIndex） | - |
| SessionsTable | sessionId | セッション管理（TTL: expiresAt, GSI: UserIdIndex） | - |
| EventStore | aggregateId / version | 振込のイベントソーシング用イベントストア | NEW_AND_OLD_IMAGES |
| OutboxTable | id / timestamp | 振込のトランザクションアウトボックス | NEW_AND_OLD_IMAGES |
| BalanceTable | accountId | CQRS 読み取りモデル（残高照会用） | - |
| AccountOpeningEventStore | aggregateId / version | 口座開設専用イベントストア | NEW_AND_OLD_IMAGES |
| AccountOpeningOutboxTable | id / timestamp | 口座開設専用アウトボックス（GSI: StatusIndex） | NEW_AND_OLD_IMAGES |

### Lambda 関数（NODEJS_22_X、関数ごとに個別 IAM ロール）

- 認証系: `online-banking-jwt-authorizer`（API Gateway TokenAuthorizer）、`online-banking-login`、`online-banking-verify-token`、`online-banking-register`
- 照会系: `online-banking-balance`、`online-banking-transactions`
- 振込系: `online-banking-transfer`、`online-banking-withdraw-worker`、`online-banking-withdraw-outbox`、`online-banking-deposit-worker`、`online-banking-deposit-outbox`、`online-banking-mail-notification`
- 口座開設系: `online-banking-account-opening`、`online-banking-account-opening-notification`、`online-banking-account-opening-outbox-processor`
- 管理者: `online-banking-admin-api`

各 Lambda ロールには CloudWatch Logs 権限と KMS 利用権限を基本として付与し、必要なテーブル・インデックス、EventBridge の `events:PutEvents`、Core Banking API 呼び出し用の `execute-api:Invoke` と API Key 取得用 `apigateway:GET` を個別に追加している。

### イベント連携（EventBridge / SQS / DynamoDB Stream）

- EventBus: `banking-event-bus`
- SQS: `DepositQueue` / `WithdrawQueue`（それぞれ DLQ 付き、maxReceiveCount = 3、visibilityTimeout 300 秒、retentionPeriod 14 日、KMS 暗号化、SSL 必須）
- EventBridge Rule:
  - `WithdrawRequested`（source: banking.transfer）→ WithdrawQueue
  - `DepositRequested`（source: banking.transfer）→ DepositQueue
  - `TransferCompleted`（source: banking.transfer）→ mailNotificationLambda
  - `AccountOpeningApplicationCreated` / `AccountOpeningApplicationCompleted`（source: banking.account-opening）→ accountOpeningNotificationLambda
- DynamoDB Stream トリガー: OutboxTable の `type=withdraw`/`type=deposit` INSERT で各 Outbox Lambda を起動、AccountOpeningOutboxTable の `status=pending` INSERT で outbox-processor を起動（フィルタ付き）

### API Gateway（Banking API, ステージ v1）

- JWT TokenAuthorizer による保護（resultsCacheTtl 5 分）
- API Key を 3 種（customer / admin / auth）作成し、それぞれ Usage Plan（スロットリング・日次クォータ）に紐付け。値は SSM Parameter Store に保存
- リクエストバリデーター（ボディ・パラメータ検証）を有効化
- アクセスログ・実行ログ（INFO）・X-Ray トレーシング・メトリクスを有効化
- WAF Web ACL（REGIONAL）を関連付け: RateLimit（5 分で 2000 リクエスト）+ AWS マネージドルール（Common / KnownBadInputs / Linux）

主なエンドポイント: `POST /api/auth/login`、`GET /api/auth/verify`、`POST /api/users/register`、`GET /api/accounts/{id}/transactions`、`GET /api/balance`、`POST /api/transfer`、`POST /api/accounts`、`GET /api/accounts/{id}`、`POST /api/accounts/confirm/{transactionId}`、`POST /api/accounts/confirm/{transactionId}/reject`、`GET /admin/account-applications`、`GET /admin/account-applications/{applicationId}/credentials`、`GET /admin/transfer-events/{transactionId}`

### KMS 構成（KmsConstruct）

- カスタマー管理キーを自動キーローテーション有効で作成（FISC 実務基準 3, 13, 30, 69 対応）
- キーポリシーは職掌分離を意識し、ルートアカウント、キー管理者（CloudFormation サービスロール等）、キー使用者（DynamoDB / S3 / Lambda / SQS / Logs サービスプリンシパル）を分離
- pendingWindow 30 日、開発環境用に removalPolicy: DESTROY

### フロントエンドスタック（OnlineBankingAppFrontendStack）

- 静的コンテンツ用 S3 バケット（非公開、バージョニング、KMS 暗号化、SSL 必須、アクセスログ有効）
- CloudFront Distribution: OAC 利用、REDIRECT_TO_HTTPS、TLS 1.2 (2021) 以上、地理的制限で日本 (JP) のみ許可、アクセスログ有効
- us-east-1 デプロイ時のみ CloudFront 用 WAF Web ACL（Common / KnownBadInputs / 日本のみ許可の GeoMatch）を作成
- SSM Parameter Store から API エンドポイントと API Key 値を取得し config.json を生成してデプロイ

### モックコアバンキングスタック（TemporaryCoreBankingSystemStack）

- DynamoDB: 顧客マスター（CoreCustomersTable）、口座マスター（CoreAccountsTable, GSI: CustomerIdIndex）、取引履歴（CoreTransactionsTable, GSI: AccountIdIndex）。いずれも KMS 暗号化・PITR・Stream 有効
- Lambda: `core-banking-api`（memorySize 512, X-Ray ACTIVE, 明示的 DLQ 付き）
- API Gateway（REGIONAL）: IAM 認証 + API Key 必須、リソースポリシーで同一アカウント・同一リージョン・`online-banking-*` ロールからのアクセスに限定。Usage Plan（rateLimit 500 / burstLimit 1000 / 日次 100,000）
- エンドポイント: `POST /api/customers`、`GET /api/customers/{customerId}`、`POST /api/accounts`、`GET /api/accounts/{accountId}`、`GET /api/accounts/{accountId}/transactions`、`POST /api/transactions/deposit`、`POST /api/transactions/withdraw`、`GET /api/transaction/{transactionId}`
- デフォルトデータ（顧客 CUST001/CUST002、口座 0011234567/0017654321 の残高 10,000,000 円、取引履歴 TXN001〜TXN005）をカスタムリソースで投入

## アプリケーション利用手順

本節は、モバイルバンキングアプリケーションのフロントエンド利用手順を示す。前提として、アプリケーションがデプロイ済みで、必要な AWS リソースが正常に稼働していること。

### 1. アプリケーションへのアクセス

デプロイが完了すると WebsiteUrl が出力される。

![デプロイ完了画面](../assets/images/app-guide/deployment-output.png)

赤枠で囲まれた WebsiteUrl のリンクをクリックして、ブラウザでモバイルバンキングアプリケーションにアクセスする。

### 2. 口座開設申込（ユーザ画面）

アプリケーションにアクセスすると、最初に以下の画面が表示される。

![アプリ初期画面](../assets/images/app-guide/app-home-screen.png)

この画面では、既存の口座をお持ちの場合はログインを、新規で口座開設を希望する場合は口座開設の申込を行うことができる。口座開設を行う場合は「口座開設を始める」ボタンを押下する。

#### 2.1 口座開設申込情報の入力

「口座開設を始める」ボタンを押下すると、口座開設申込画面に遷移する。

![口座開設申込画面](../assets/images/app-guide/account-opening-form.png)

この画面では、お名前（姓・名）、生年月日、住所、電話番号、メールアドレス、その他必要事項を入力する。すべての必要な情報を入力したら「入力内容を確認する」ボタンを押下する。

#### 2.2 申込内容の確認

入力内容確認画面では、先ほど入力した情報が表示される。

![申込内容確認画面](../assets/images/app-guide/account-opening-confirmation.png)

内容に間違いがないことを確認し、問題がなければ「申込を確定する」ボタンを押下する。

#### 2.3 口座開設申込完了

申込確定後、受付完了画面が表示される。

![口座開設申込受付完了画面](../assets/images/app-guide/account-opening-completed.png)

申込内容は管理者による承認待ちの状態となり、承認後に口座が開設される。

### 3. 口座開設申請の承認（管理者画面）

![アプリホーム画面](../assets/images/app-guide/app-security-home.png)

管理者画面に切り替えるため、画面左上のトグルボタンを押下する。これにより管理者モードに切り替わる。

#### 3.1 口座開設申請一覧の確認

![口座開設審査画面](../assets/images/app-guide/admin-account-review.png)

承認待ちの申請一覧が表示される。承認を行う場合は、対象の申請の「承認」ボタンを押下する。

#### 3.2 承認処理の実行

![口座開設申請承認画面](../assets/images/app-guide/admin-approval-form.png)

承認に関するコメントを入力し、「承認する」ボタンを押下する。

#### 3.3 承認処理中

![承認処理中画面](../assets/images/app-guide/admin-processing.png)

システムが承認処理を実行している間、この画面が表示される。

#### 3.4 ID/パスワード発行完了

![ID/パスワード発行完了画面](../assets/images/app-guide/admin-credentials-issued.png)

口座開設が承認され、ユーザー用のログイン ID と初期パスワードが自動生成される。「ID/パスワード」ボタンを押下して発行された認証情報を確認する。

#### 3.5 発行されたログイン情報の確認

![ログイン情報表示画面](../assets/images/app-guide/admin-user-credentials.png)

表示されたログイン ID と初期パスワードを使用して、ユーザーはアプリケーションにログインできる。これらの情報は適切な方法でユーザーに通知する。

### 4. ログイン（ユーザ画面）

アプリのトップ画面から「ログイン」ボタンを押下して、ログイン画面に遷移する。

![ログイン画面](../assets/images/app-guide/user-login-screen.png)

発行されたログイン ID と初期パスワードを入力し、「ログイン」ボタンを押下する。ログインが成功するとダッシュボード画面が表示される。

![ダッシュボード画面](../assets/images/app-guide/user-dashboard.png)

この画面では、口座残高や取引履歴などの情報を確認できる。

#### 4.4 デモユーザーでの体験

口座開設を行わなくても、デモユーザーで簡単にアプリの機能を体験できる。

![デモユーザー選択画面](../assets/images/app-guide/demo-user-selection.png)

「ユーザー 1」または「ユーザー 2」を選択することで、サンプルデータでアプリケーションの機能を確認できる。

![デモユーザーダッシュボード画面](../assets/images/app-guide/demo-user-dashboard.png)

### 5. 振込・送金（ユーザ画面）

ログイン後のダッシュボード画面から振込・送金の操作を行う。

![ダッシュボード画面](../assets/images/app-guide/transfer-dashboard.png)

画面上の「振込・送金」ボタンを押下して、振込機能を開始する。

![振込・送金入力画面](../assets/images/app-guide/transfer-input-form.png)

振込先口座情報、振込金額、振込目的・内容、その他必要事項を入力し、「確認画面へ」ボタンを押下する。

![振込内容確認画面](../assets/images/app-guide/transfer-confirmation.png)

振込先口座、金額、内容などに間違いがないことを確認し、問題がなければ「振込を実行」ボタンを押下する。

![振込完了後のダッシュボード画面](../assets/images/app-guide/transfer-completed-dashboard.png)

振込処理が完了すると、ダッシュボード画面に戻り、最近の取引履歴と現在の残高が更新される。

### 6. 振込処理イベント参照（管理者画面）

振込処理が完了した後、管理者は取引の詳細な処理フローを確認できる。取引履歴に表示される Transaction ID をコピーし、画面左上のトグルボタンで管理者画面に切り替え、「振込処理イベント参照」機能にアクセスする。

![振込処理イベント参照画面](../assets/images/app-guide/admin-transaction-events.png)

取引 ID 入力欄に Transaction ID を貼り付けて「検索」ボタンを押下すると、該当する取引の詳細な処理履歴（取引の各ステップ、処理時刻、処理状況、詳細情報）が表示される。この機能により、管理者は取引処理の透明性を確保し、必要に応じてトラブルシューティングを行うことができる。
