---
name: fisc-to-aws-security-agent
description: >-
  Deterministically generates source documents (Markdown) from the FISC "Security Guidelines
  on Computer Systems for Financial Institutions" (安対基準 / Antai Kijun) PDF for import into
  AWS Security Agent as Custom security requirements packs. It converts a ~36MB PDF to text,
  extracts standard items, selects workload-relevant technical controls, splits them into
  thematic packs (<=20 items and <=2MB each), and describes each item in the 5-field structure
  name/description/applicability/compliance/remediation. Use this skill when a user asks to
  "import the FISC安対基準 into Security Agent", "create FISC custom requirement packs",
  "convert the 安対基準 PDF for Security Agent", or Japanese equivalents such as
  「FISC安対基準をSecurity Agentに取り込みたい」「FISCのカスタム要件パックを作りたい」
  「安対基準PDFをSecurity Agent用に変換して」. Output is reproducible; the same input always
  yields the same output.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0.0"
---

# FISC 安対基準 → AWS Security Agent Custom Requirements Conversion Skill

> Japanese version / 日本語版: [SKILL_ja.md](SKILL_ja.md)
> `SKILL.md` (this file, English) is the authoritative skill definition. `SKILL_ja.md` is a
> same-content Japanese mirror. Japanese users may rename `SKILL_ja.md` to `SKILL.md` to use it.
> Both files are maintained by the coding agent (Kiro), not edited by hand.

Given a FISC 安対基準 PDF as input, this skill generates source documents (Markdown) that can be
imported into AWS Security Agent as **Custom security requirements packs**.

The design goal is that **anyone who runs it gets the same result (deterministic and reproducible)**.
Classification uses an explicit definition file and field generation uses templates, so it does not
depend on ad-hoc LLM judgment.

---

## Assumptions and Constraints (must follow)

- **The operator supplies the input PDF.** This skill does not bundle any copyrighted PDF in the repository.
- **Security Agent evaluates at the workload (app/code/design) level.** Therefore, among the FISC
  standards, facility standards (physical facilities), audit standards (audit processes), and purely
  organizational/personnel controls are **excluded by default** (policy B: select workload-relevant
  technical controls). The focus is technical items of the practice standards plus control standards.
- **Field character limits** (Security Agent spec): name 80 / description 500 /
  applicability 10,000 / compliance criteria 10,000 / remediation guidance 10,000 (characters).
- **At most 20 items per pack**, and **each file <= 2MB** (upload constraints).
- Output is a draft. **After import, review and adjust the content in Security Agent.**
- Always refer to `reference.md` for detailed specs, pack definitions, exclusion policy, and customization.

---

## Workflow

```
FISC PDF
  → 1. extract_pdf : full-text extraction (with page markers)
  → 2. build_items : structured extraction of standard items (統/実/設/監 + number, title/summary/body/page)
  → 3. classify    : deterministic classification into 6 thematic packs per pack_mapping.json (non-matching excluded)
  → 4. generate    : convert each item into 5-field Markdown (1 item = 1 section)
  → 5. validate    : machine-check character counts, item count (<=20), and file size (<=2MB)
  → output/*.md    → upload to Security Agent Custom packs
```

## Usage

### One-shot run (recommended)

```bash
python3 ~/.kiro/skills/fisc-to-aws-security-agent/scripts/run_all.py \
    --pdf "<path to FISC 安対基準 PDF>" \
    --outdir ./output
```

- `output/NN_<pack_id>.md` is generated per pack, and `output/manifest.json` lists them.
- `--max-items` sets the per-pack limit (default 20); `--workdir` changes the intermediate output dir.
- Validation runs last; `✅ 検証OK` means all constraints are satisfied (exit code 1 on failure).

### Running individual steps

For troubleshooting or partial re-runs, run each script individually (see `reference.md`).

### Choosing the output format (upload vs manual registration)

`generate_packs.py` supports two output formats via `--format`.

- `--format upload` (default): one file per pack, to be **uploaded** to Security Agent for automatic
  requirement generation.
- `--format manual`: for **manually registering one item at a time in the console**. Each item's five
  fields (name / description / applicability / compliance / remediation) are split into copy-paste-ready
  `text` code blocks, annotated with **current character count and limit**, and **FISC category / source page**.

> On upload, Security Agent's automatic reinterpretation may split/merge items, translate to English,
> truncate descriptions, and lose FISC numbers (traceability). **If fidelity to the FISC original text
> and an audit trail are priorities, use `--format manual` for manual registration.**

Example of generating the manual format (regenerated from the intermediate `classified.json`, no PDF needed):

```bash
python3 ~/.kiro/skills/fisc-to-aws-security-agent/scripts/generate_packs.py \
    --classified ./output/_work/classified.json \
    --config ~/.kiro/skills/fisc-to-aws-security-agent/config/pack_mapping.json \
    --outdir ./output_manual \
    --format manual
```

### Adding AWS remediation guidance to the remediation field

For each requirement's **remediation guidance**, in addition to the FISC commentary source, this skill
appends the **AWS-proposed remediation ("What the customer should control" + "Supplementary information")**
(derived from the AWS-authored "FISC Security Guidelines Reference". **The "AWS response status" column is
NOT used**).

- The AWS data is stored in the skill-bundled config file **`config/aws_remediation_v<version>.json`**.
  This config holds **only AWS-authored columns** and **does not include any FISC 安対基準 body/commentary text**.
- `generate_packs.py` automatically selects the **highest version** among `config/aws_remediation_v*.json`.
- For each item code, it looks up AWS rows by both **exact match** (e.g. `実14-1`) and **base code**
  (`実14` with `-N` removed), de-duplicates, and appends them.
- To disable or pin: `--no-remediation` (do not append), `--remediation-config <path>` (pin a version).

**Generating the config file (from the AWS reference PDF):**

```bash
python3 ~/.kiro/skills/fisc-to-aws-security-agent/scripts/build_remediation_config.py \
    --pdf "<AWS-authored FISC reference.pdf>" \
    --version 13 \
    --out ~/.kiro/skills/fisc-to-aws-security-agent/config/aws_remediation_v13.json
```

### Replacement procedure when the 14th edition is published

When the AWS reference PDF for the 14th edition is published, the following switches over automatically
(do not bundle or store the FISC 安対基準 body PDF):

1. Run `build_remediation_config.py` against the **14th-edition PDF** with `--version 14 --out config/aws_remediation_v14.json`.
2. Place the generated `config/aws_remediation_v14.json` in the skill's `config/`.
3. From then on, `generate_packs.py` **auto-selects the highest version, v14** (the old v13 may be removed or kept).
4. Regenerate with `--format manual` etc., and the remediation guidance updates to the 14th-edition AWS content.

## Import procedure into Security Agent (performed by the operator)

### A. Import via upload (`--format upload`)

1. In the AWS Console, open **AWS Security Agent → Security requirements**.
2. On the **Custom security requirements packs** tab, create a pack with **Create security requirements pack**
   (recommended: name it to match the file, e.g. `FISC-01…`).
3. For the target pack, upload one `NN_*.md` via **Choose files** and click **Generate requirements**.
4. Security Agent generates requirements from the document. After generation, **review/edit** the content and activate.
5. Repeat 2–4 for each of the 6 packs.

> Note: Uploading a new document to an existing pack **regenerates and replaces all** requirements in that pack.

### B. Register manually, one item at a time (`--format manual`, recommended for FISC fidelity / audit trail)

1. Generate `output_manual/NN_*.md` with `--format manual` (see the example above).
2. In the AWS Console, open **AWS Security Agent → Security requirements → Custom security requirements packs**
   and create a pack with **Create security requirements pack**.
3. In the pack, choose **Add requirement** (manual add) and copy-paste each item's five `text` code blocks
   (①name–⑤remediation) into the corresponding fields in order.
4. Each block shows its **current character count and limit**, so confirm it is within the limit before saving/activating.
5. Each item heading records the **FISC category / source page**, so keep the mapping between the registered
   requirement and the FISC clause (traceability) in a ledger.
6. Repeat 3–5 for all items across all 6 packs.

> Manual registration avoids Security Agent's automatic reinterpretation, so FISC numbers, source text, and
> remediation guidance are preserved as-is.

## Customization

- **Adjusting target items / reorganizing packs**: edit each pack's `include` (array of FISC numbers) in
  `config/pack_mapping.json`. Putting the same number in multiple packs is rejected by validation (for determinism).
- **Covering all FISC items (policy A)**: setting `selection_mode` to `keyword` also auto-classifies items not
  in `include` by keyword (note this mixes in facility/audit/organizational items and increases non-evaluable items).
- After changes, re-run `run_all.py` to reproduce the same result from the same input every time.

## Security (threat-model response)

This skill addresses findings from a STRIDE threat-model review and implements the following controls.

**Integrity / tamper detection**
- `run_all.py` records the SHA-256 of each stage's intermediate artifact (`fisc_full.txt`/`items.json`/
  `classified.json`) and of the config, and re-verifies right before the next stage reads them (inter-stage tamper detection).
- `validate.py` **regenerates the actual `output/*.md` from classified/config and compares them**, and also
  cross-checks against the SHA-256 in `manifest.json` (detects post-generation `.md` edits or staleness).
- `generate_packs.py` records the SHA-256 of each `.md` in `manifest.json`.
  **Immediately before upload, always confirm each manifest SHA-256 matches the actual file.**

**Input authenticity**
- Passing `--pdf-sha256 <hex>` verifies the input PDF's SHA-256 before parsing and aborts on mismatch
  (supported for both the FISC PDF and the AWS reference PDF: `extract_pdf.py`, `build_remediation_config.py`).
- The generated `aws_remediation_v<version>.json` records the source PDF's `source_pdf_sha256`.

**Execution-environment hardening**
- All artifacts are `umask 0077` + `chmod 0600` (owner-only).
- Input/output paths are `realpath`-canonicalized, and outputs are guaranteed not to overwrite `scripts/` or
  `config/` (path-traversal defense).
- The `pdftotext` fallback is resolved via `shutil.which` and only an absolute path under an allowlisted system
  directory is executed (PATH-poisoning defense). `--require-pymupdf` disables the fallback entirely.
- On PyMuPDF fallback, an explicit warning is printed to stderr and the extraction method is recorded in
  `fisc_full.txt.meta.json`.
- `PyMuPDF` is pinned in `scripts/requirements.txt` (`pip install -r scripts/requirements.txt`).
- Shared logic is consolidated into `fisc_lib.py` (no import-time side effects), eliminating unintended
  code-execution paths via `validate.py`'s import.
- PDF-derived text is neutralized against Markdown/code-fence injection (no effect on legitimate Japanese text).

**Non-repudiation / audit**
- On each run, `run_all.py` emits `run_manifest.json` (run_id, timestamp, operator, arguments, and SHA-256 of
  the input PDF/config/intermediates/outputs) and appends to `run_log.jsonl` (append-only).

**Controls required on the operator side (outside code, performed by the operator)**
- **Require MFA on the IAM principal** used to upload to AWS Security Agent, and apply a **least-privilege policy**
  scoped to only the required Security Agent actions/resource ARNs (credential-theft defense).
- Keep `scripts/` and `config/` (`pack_mapping.json`, `aws_remediation_v*.json`) **under version control with
  restricted commit rights**. Tampering is detectable via the `run_manifest` hashes.
- Verify the input PDF with `--pdf-sha256` using a SHA-256 from a trusted source.
- To pin the remediation config, specify it explicitly with `--remediation-config <path>`, or fix the expected
  hash with `--remediation-sha256 <hex>` (aborts on mismatch; defends against higher-version config injection).
- Output is a "pre-review draft". Manually review the content and manifest hashes before upload.

## Guardrails

- Do not alter FISC original requirement text/commentary; place it into fields as-is (no misinterpretation or fabrication).
- Content exceeding the character limit is explicitly truncated at the end (`…(以下略。出典参照)`), always with the source cited.
- **The FISC 安対基準 body/commentary PDF is NOT bundled or stored in the skill** (the operator supplies it each time).
- The AWS remediation config holds **only the AWS-authored "What the customer should control" and "Supplementary
  information" columns** and does not include FISC body text (the "AWS response status" column is not used).
- Output is a "pre-review draft" and assumes human review after import into Security Agent.
