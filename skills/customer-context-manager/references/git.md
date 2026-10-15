# Git Version Control for the Context Store

Setup and behaviour of the store's git repository, referenced from SKILL.md.

Japanese version: [git_ja.md](git_ja.md)


When `git_enabled: true` (default), the data directory is managed as a git repository:

## Setup
- On first-time setup, run `git init` in the data directory if not already a repo
- Create a `.gitignore` if needed (empty by default — track everything)
- Do not configure a remote automatically. The repository stays local unless the user
  explicitly asks for a backup remote

## Auto-Commit
- After every context update (file create or modify), stage the changed files
  and commit with a descriptive message
- Commit message format: `update <customer-slug>/<file>: <brief description>`
- **Keep personal names, contact details, and confidential specifics out of commit
  messages.** Anything written there is retained in history and cannot be redacted by a
  later edit. Describe the change by category and count instead:
  - `update any-bank/people: add 1 contact (Digital Banking)`
  - `update any-bank/terms: add 1 term`
  - `update index: register new customer`
- Batch multiple changes in a single conversation into one commit when practical

## Benefits
- Full history of context changes with timestamps
- Ability to diff and revert incorrect updates

## Remote Backup
Pushing to a remote copies customer-confidential data off this machine, so it is opt-in
and constrained:

- Only a remote approved by your organization for this data class, and only a private
  repository. Personal accounts and public repositories are not acceptable
- The user configures the remote deliberately; this skill never adds one on its own
- Verify visibility is private before the first push. Once pushed, history — including any
  name or figure that slipped into a commit message — is outside your control

## Disabling
Set `git_enabled: false` in config.md to disable. No git operations will be performed.
This also removes the only audit trail and the only undo mechanism for context changes:
updates and deletions become untraceable, and a wrong merge is unrecoverable. If you
disable it, arrange another form of backup and inform the user of the tradeoff.
