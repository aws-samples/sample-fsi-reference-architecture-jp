<!-- Fictional example. Part of customer-context-manager's example store, not real data. -->
# Customer Index

<!--
Aliases is the name-resolution entry point. Put *every* name a human or an internal tool
might use for this customer here, so the customer is found no matter which name appears:
abbreviations and informal shorthand, the formal legal name and its short form, Japanese
and English names, former names kept after a rename, group and brand names, and the name
registered in an internal CRM if it differs from reality.
If a lookup ever fails for what turns out to be a known customer, add that name here.
Group captures corporate group relationships. Use `-` for standalone customers.
Status: Active | Archived.
This is the one file without a Source column: it is a resolution registry, not a set of
facts, and it is loaded on every task. Alias provenance goes on the `Common aliases` line
in that customer's profile.md.
-->

| Slug | Display Name | Aliases | Industry | Group | Status |
|------|-------------|---------|----------|-------|--------|
| any-manufacturing | Any Manufacturing Co., Ltd. | エニー製作所, エニー製作所株式会社, Any Manufacturing, 旧エニー鉄工所, AM | Precision Parts Manufacturing | エニーグループ | Active |
| any-group-trading | Any Group Trading Co., Ltd. | エニー商事 | Trading | エニーグループ | Active |
| any-construction | Any Construction Inc. | エニー建設 | Construction | - | Active |
| former-ironworks | Former Ironworks Co. | 旧エニー鉄工所（法人格消滅） | Manufacturing | エニーグループ | Archived |
