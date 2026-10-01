# お客様の改称・統合・分割

SKILL.md から参照される手順書。実行前に本ファイルを読むこと。ただし SKILL.md 側のガードレール
（計画の提示、ユーザー確認、gitのクリーンな状態、同一性の確認）を満たした後に限る。

English version: [renaming-merging.md](renaming-merging.md)

お客様を**改称**する場合（slug `<old>` → `<new>`）:

1. **ディレクトリを移動** `customers/<old>/` → `customers/<new>/`（git有効時は `git mv`
   で履歴を保つ）。
2. **`index.md` を更新**: 新しい Slug と表示名にし、**旧名と旧 slug を Aliases に追加**して
   旧名でも引けるようにする。
3. **`profile.md` に変更を記録**: 改称/合併/分社の内容と日付を Basic Information か Notes に
   記す（何が何になったか、理由）。
4. **流入参照を修正**: データディレクトリ内で旧 slug/旧名を検索し、それを指す箇所をすべて
   更新する — 例: `people/partners.md` の Customers 列、他のお客様ファイル内のグループ親子
   参照、（内部コンパニオン有効時は）`internal-config.md` のアカウントグルーピング。
5. **コミット**: 意図が分かるメッセージにする（例: `rename any-bank → any-bank-renamed: company
   renamed 2026-04-01`）。

2社が**統合**する場合（2 → 1）:

- 残す slug = 新しい/正しい社名 とする。
- 消える側のファイル内容を残す側にマージする（履歴・人・systems — 蓄積した情報を失わない）。
- 消える側の slug・表示名・旧 Aliases を残す側の Aliases に集約する。
- 合併と日付を `profile.md` に記録し、旧ディレクトリと index 行を削除する（`git mv`/commit で
  履歴は残す）。

**分社・分割**（1 → 2）の場合は、新しいお客様エントリを作成し、関連する共有コンテキストを
コピーし、両者の Aliases/profile で相互参照して系譜を辿れるようにする。

指針: slug と表示名は常に *現在の正しい* 名前を反映し、Aliases と profile.md が *履歴* を
保持して旧名でも解決できるようにする。
