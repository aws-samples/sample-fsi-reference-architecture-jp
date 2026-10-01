# BLEA for FSI と BLEA の差異

本ドキュメントは BLEA for FSI と BLEA（Baseline Environment on AWS）の差異を記述する。出典は
`doc/governance-base/diff-from-blea.md`。

BLEA for FSI はセキュアなベースラインを確立するためのリファレンス CDK テンプレート群である BLEA のマルチアカウント版
（v2.0.0）をベースに、FISC 準拠の観点から金融ワークロードに必要とされる下記の要素（CDK テンプレート実装 および
ガイダンス）を追加している。異なるアセットとして開発を行っているが、セキュアなベースラインの確立という観点では今後も
BLEA をリファレンス実装として参考にしていく方針である。

## BLEA に対して追加した要素

- 閉域網での CDK 実行環境
- FISC 実務基準に沿った Control Tower ガードレールでの対策（[fisc-mapping.md](fisc-mapping.md) を参照）
- 大阪リージョンへのガバナンスベースのデプロイ（[deployment.md](deployment.md) を参照）
- AWS IAM Identity Center（旧 AWS SSO）の MFA 設定
- FISC 実務基準対策一覧
  - 勘定系
  - 顧客チャネル
  - オープン API
  - マーケットデータ
  - データ分析プラットフォーム
- ガバナンスベース CDK テンプレート
  - CloudTrail S3 データイベント記録
  - SSM セッションマネージャーの S3 ログ出力
- 金融ワークロード CDK サンプルコード
  - 勘定系
  - 顧客チャネル
  - オープン API
  - マーケットデータ
  - データ分析プラットフォーム

## BLEA から削除した機能

- Slack 通知機能
