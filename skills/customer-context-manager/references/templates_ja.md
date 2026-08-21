# コンテキストファイルのテンプレート

`customer-context-manager` が管理する各コンテキストファイルの最低限の構造。
期待される密度と品質の記入例は [sample-context.md](sample-context.md) を参照。

English version: [templates.md](templates.md)

### index.md

```markdown
# Customer Index

| Slug | Display Name | Aliases | Industry | Group | Status |
|------|-------------|---------|----------|-------|--------|
| any-bank | Any Bank | AB | Banking | Any Group | Active |
| any-securities | Any Securities | AS | Securities | Any Group | Active |
| any-insurance | Any Insurance | AI | Insurance | - | Active |
```

Group列は企業グループの関係性（親会社、系列、持株会社の関連）を表す。
単独のお客様には `-` を使用する。

**Aliases は名前解決の入口である。** 会話中（あるいは社内ツール上）でこのお客様を指して
使われ得る呼称を *すべて* ここに入れる。どの名前が出てきても引けるようにするため:

- 略称・通称（例: `AB`）
- 正式な法人名と短縮形（例: `株式会社` / `Inc.` の有無）
- 日本語名・英語名
- **改称後も残す旧称**（旧名でも引けるように）
- グループ名・ブランド名としての呼称
- 現実と異なる社内CRM上の登録名（内部コンパニオンスキルがここに書き戻す）

既知のお客様であるはずの名前で解決に失敗したら、その名前を Aliases に追加し、次回の
照合が成功するようにする。

### customers/<slug>/profile.md

```markdown
# <Display Name>

## Basic Information
- Formal name: 
- Common aliases: 
- Industry: 
- Size: 
- Headquarters: 
- Website: 

## Relationship Summary
- First engagement: 
- Current status: 
- Primary contact: 

## Revenue
<!-- 営業側の財務情報：契約、取引規模、利用額。社外には開示しない -->

## Strategic Context
<!-- お客様のビジネス優先事項と自社エンゲージメントとの関係 -->

## Notes
```

### customers/<slug>/people.md

```markdown
# People — <Display Name>

## Customer Contacts

| Name | Department | Title | Role in Decisions | Email | Notes |
|------|-----------|-------|-------------------|-------|-------|

## Partner Contacts

このお客様の特定プロジェクトにアサインされているパートナー。

| Name | Company | Role | Project/Context | Email | Notes |
|------|---------|------|-----------------|-------|-------|
```

### customers/<slug>/organization.md

```markdown
# Organization — <Display Name>

## Current Structure
<!-- 自社のエンゲージメントに関連する組織階層を記述 -->

## Decision-Making Flow
<!-- 誰が何を承認するか：技術判断、予算、契約 -->

## Key Departments

## Change History
<!-- 組織再編を追跡する。新しいものが上。 -->

### YYYY-MM-DD: <変更内容>
- Old: <旧構造>
- New: <新構造>
- Impact: <エンゲージメントへの影響>
```

### customers/<slug>/systems.md

```markdown
# Systems & Technology — <Display Name>

## Known Systems

| System Name | Category | Technology | Notes |
|-------------|----------|-----------|-------|

## Technical Constraints
<!-- 規制要件、セキュリティポリシー、ネットワーク制約 -->

## Technology Preferences
```

### customers/<slug>/history.md

```markdown
# History — <Display Name>

重要な転換点のみ記録する — 定例会議のログではない。
詳細な活動履歴はCRMが利用可能であればそちらを参照する。

## Key Events

### YYYY-MM-DD: <Event Title>
- What happened: 
- Significance: 
- Impact on relationship: 

## Past Proposals

| Date | Topic | Outcome | Reason |
|------|-------|---------|--------|
```

### customers/<slug>/terms.md

```markdown
# Terminology — <Display Name>

## Glossary

| Term | Meaning | Context | Date Added |
|------|---------|---------|------------|
```

### customers/<slug>/notes.md

```markdown
# Notes — <Display Name>

## Communication Preferences
- Preferred channel: 
- Response patterns: 
- Meeting preferences: 

## Competitive Landscape
<!-- 他ベンダー、競合ソリューション。社外には開示しない -->

## Sensitivities
<!-- 慎重に扱うべきトピック、過去のネガティブな経験。社外には開示しない -->

## Free Notes
```

### people/internal.md

```markdown
# Internal Team Members

複数のお客様対応に関わる可能性のある社内メンバーを管理する。

| Name | Role | Expertise | Notes |
|------|------|-----------|-------|
```

### people/partners.md

```markdown
# Partner Companies

お客様横断のパートナー情報。プロジェクト固有のアサインは各お客様のpeople.mdを参照。

| Company | Relationship | Domains | Key Contacts | Customers |
|---------|-------------|---------|--------------|-----------|
```
