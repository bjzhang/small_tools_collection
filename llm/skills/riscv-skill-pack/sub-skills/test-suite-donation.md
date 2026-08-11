---
name: riscv-skill-pack/test-suite-donation
version: "1.0"
updated: "2026-08-11"
description: >
  Engineering workflow for donating test suites (e.g., H-ext, Vector) to
  upstream RISC-V test repositories (riscv-arch-test, act4 branch). Covers
  contribution lifecycle, .gitignore gotchas, cross-platform shell issues,
  and coverage engineering methodology. Activate when contributing test
  suites to RVI/Task Groups or auditing coverage before PR submission.
license: Apache-2.0
---

# Test-Suite Donation Sub-Skill

> **Source**: Distilled from T243 H-ext donation (2026-08), covering act4
> branch workflow, coverage audit (F-1~F-10), and cross-platform engineering
> gotchas. Applies to any future extension test-suite donation (H, Vector,
> Matrix, etc.).

## When to Use

- Contributing test suites to upstream `riscv/riscv-arch-test` (act4 or similar branch)
- Setting up donation branches for H-ext / Vector / other extension test suites
- Auditing coverage points before PR submission to RVI Task Groups
- Cross-platform shell scripting for test generation/maintenance (macOS + Linux)

---

## §1 Upstream Contribution Workflow

### 1.1 Initial Setup

1. **Shallow clone upstream** (avoid nested-repo pollution):
   ```bash
   git clone --depth 1 -b <branch> <upstream-url> <local-path>
   ```
2. **Exclude nested clone** from parent repo (critical — otherwise parent git status floods):
   ```
   # In parent .gitignore
   Cooperation_RD/RVA23-contribution-to-RVI/riscv-arch-test/
   ```
3. **Create donation branch** off upstream:
   ```bash
   git checkout -b <descriptive-name> origin/<branch>
   ```
   Naming convention: `<ext>-from-<source>` (e.g., `h-ext-from-wtze`).

### 1.2 Commit Discipline

- **Single initial commit** for original materials — keeps donation history clean.
- **Message format**: follow upstream convention.
  - riscv-arch-test example: `[RFD] <Extension> Test Suite Donation`
- **Commit body** should list file count + insertion count for reviewer quick-scan.
- **Do NOT mix** setup commit with later audit fixes — separate concerns.

### 1.3 PR Preparation Checklist

- [ ] All files tracked (no silent .gitignore drops — see §2.1)
- [ ] `reports/` and `elfs/priv/` target dirs exist (`mkdir -p` if missing — see §2.2)
- [ ] Coverage points align with covergroups (see §3)
- [ ] Cross-platform shell verified (see §2.3)
- [ ] `.gitignore` audit done after every copy batch

---

## §2 Engineering Gotchas

### 2.1 Upstream .gitignore Swallows New Files ⚠️

**Symptom**: After copying N files, `git status` shows fewer than N untracked.

**Detection command**:
```bash
git check-ignore -v path/to/suspicious/file
# Output: <source-line-number>:<rule>  <path>
```

**Concrete case (riscv-arch-test act4 branch)**:

Upstream `.gitignore` line 38:
```
tests/priv/**/*.S
```
with two negation exceptions:
```
!tests/priv/pmp/**/*.S
!tests/priv/*Sv*/**/*.S
```

**Implication**: Any new extension whose test dir name doesn't contain `Sv` and isn't `pmp` will be **silently ignored**. H-ext, Vector, Matrix all fall into this trap.

**Workaround hierarchy**:
1. **Immediate**: `git add -f tests/priv/<X>_*.S` — minimal disruption, git keeps tracking.
2. **For PR discussion**: propose adding `!tests/priv/<X>_*.S` negation rule to upstream `.gitignore` in a separate commit (signals intent).
3. **Not viable**: renaming test dir to match `*Sv*` pattern (breaks extension naming).

**Lesson**: After every copy batch, audit:
```bash
git check-ignore -v tests/priv/**/*.S
```
Empty output = all files tracked.

### 2.2 Missing Target Directories

**Symptom**: Upstream checkout lacks `elfs/priv/` or `reports/`.

**Fix**:
```bash
mkdir -p elfs/priv reports
```

No issue, just note that upstream layout does not pre-contain all donation target directories. Always verify before `cp`.

### 2.3 BSD sed vs GNU sed (Cross-Platform) ⚠️

**Gotcha**: macOS `/usr/bin/sed` (BSD) does **not** support BRE `\+` quantifier. Silently produces wrong output.

**Broken on macOS** (appears to work on Linux):
```bash
sed 's/x[0-9]\+/xR/g' file.txt
```

**Portable alternatives** (choose one):
```bash
# Option A: explicit repetition (BRE, works everywhere)
sed 's/x[0-9][0-9]*/xR/g' file.txt

# Option B: extended regex via -E (cleaner, recommended)
sed -E 's/x[0-9]+/xR/g' file.txt
```

**Concrete case**: During register-normalization diff for H-ext coverage audit, first version used `\+` and mistakenly concluded hgatp duplication was only 36% (actual: much higher). Multi-digit register suffixes (`x12`, `x23`) were not normalized, skewing the redundancy count.

**Lesson**:
- Always use `sed -E` for cross-platform scripts.
- Or test scripts on both BSD and GNU sed before trusting output.
- Common BSD/GNU differences: `\+`, `\?`, `\|`, `\b`, `\s`.

---

## §3 Coverage Engineering Methodology

### 3.1 "Redundancy ≠ Deletion" Principle ⚠️

Apparent duplication in test suites (e.g., M-mode and HS-mode blocks with identical structure) often reflects **legitimate coverage of separate covergroups**.

**Rule**: Each line in a coverage test corresponds to a valid covergroup bin sample. Apparent duplication at the test-code layer is usually mandated by parallel covergroups at the model layer.

**True optimization path**:
- ❌ Wrong: delete "duplicate" test code
- ✅ Right: merge covergroups at the coverage model layer (e.g., combine `H_mcsr_cg` + `H_hscsr_cg` into unified covergroup with mode cross-bins)

**Concrete case**: H_workspace bitwalk has M/HS clones (~30%, 12179/41086 lines). Both are required because the coverage model defines `H_mcsr_cg` (M-mode CSR) and `H_hscsr_cg` (HS-mode CSR) as **parallel covergroups**. Deleting HS clone would leave `H_hscsr_cg` bins unsampled.

### 3.2 Bitwalk Walking-1 Is Minimal Complete Set

For CSR coverage, the standard `walking-1` pattern via `slli` shift is the **theoretical minimum complete set**:
- 64 set operations + 64 clear operations = 128 per CSR
- No cartesian product explosion
- Each bit toggled exactly once (each bit's set/clear independently observed)

**Verification signature**: A well-formed bitwalk CSR block is **exactly 911 lines** (64 set + 64 clear + setup/restore/macro overhead). Any deviation suggests missing cases or redundant expansions.

**Exception**: `hstatus` is the only H CSR **without** bitwalk (walk_M = walk_HS = 0). It relies on aggregate-CSR coverage points (`cp_hcsr_access`) instead.

### 3.3 Coverage Point "不可删" Judgment Checklist

Before deleting any "redundant" coverage point, verify ALL of these:

1. **Does it cover CSR-level aggregate access?** Bitwalk covers per-bit, not aggregate values (`csrrw`, `csrrc`, `csrs` patterns). Aggregate points are NOT redundant with bitwalk.
2. **Is it the only M-mode or HS-mode coverage for that CSR?** If yes, deletion breaks mode coverage.
3. **Would removing it leave a covergroup bin unsampled?** Cross-check against the coverage model definition.
4. **Does the CSR have bitwalk at all?** CSRs without bitwalk (like `hstatus`) depend entirely on aggregate coverage points.

**Concrete case**: `cp_hcsr_access` appears redundant with bitwalk at first glance, but:
- 4 operations (`csrrw1/csrs_all/csrrc_all/...`) test aggregate values — bitwalk doesn't cover aggregates
- It's the **M-mode only** CSR-level coverage for `hstatus`
- `hstatus` has no bitwalk (the only such H CSR)
- **Conclusion: 不可删**

### 3.4 Finding Severity Classification

When auditing coverage findings, classify by remediation cost:

| Severity | Meaning | Action |
|----------|---------|--------|
| **HIGH** | Wrong coverage model, will miss real bugs | Must fix before donation PR |
| **WARNING** | Suboptimal but not wrong | Document, fix in follow-up |
| **EXCLUDED** | Initial flag was wrong after re-audit | Record exclusion rationale |
| **ADJUSTED** | Direction of original finding shifted | Re-document with new direction |
| **NEW→merged** | New finding merged into existing as root cause | Update existing finding, don't duplicate |

---

## §4 Case Study: T243 H-ext Donation (2026-08)

### Context
- **Source**: WTZe's H-ext test suite
- **Target**: `riscv/riscv-arch-test` act4 branch
- **Scope**: 13 original files, 43011 insertions
- **Branch**: `act4-h-ext-from-wtze`
- **Initial commit**: `aaaf506`

### Engineering Decisions Applied

1. **Nested clone excluded** via `bosc/.gitignore` rule
2. **`git add -f tests/priv/H_workspace_h-00.S`** — force-tracked because upstream `.gitignore` line 38 swallows it (see §2.1)
3. **Flagged for donation review**: recommend option (b) — add `!tests/priv/H_*.S` negation rule in separate upstream commit before opening PR

### Coverage Audit (F-1 to F-10 Summary)

| F# | Severity | Covergroup | Issue |
|----|----------|-----------|-------|
| F-1 | EXCLUDED | H_hscsr_cg | hstatus.SPV bit position — re-audit confirmed correct |
| F-2 | ADJUSTED | H_inst_cg | VU-mode mret — real issue is F-9 (U-mode missing) |
| F-3 | HIGH | H_hscsr_cg | hstatus.vgein bin value 1/63 → wrong bit range |
| F-4 | HIGH | H_hscsr_cg | vscause_code [16:64]≠interrupt — deviates from per-cause convention |
| F-5 | EXCLUDED | H_inst_cg | cp_sret_vs VTVM — re-audit confirmed correct |
| F-6 | WARNING | H_inst_cg | HFENCE mode — needs priv_mode_hs (not m_s) |
| F-7 | WARNING | H_mcsr_cg | M-mode read-only CSR write_pattern |
| F-8 | NEW→merged | H_inst_cg | priv_mode_u missing → merged into F-9/F-10 |
| F-9 | HIGH | H_inst_cg | cp_mret_illegal priv_mode_hs_vs_vu missing U-mode |
| F-10 | HIGH | H_inst_cg | cp_sret_illegal priv_mode_vu missing U-mode |

**Key insight**: F-1, F-2, F-5, F-6, F-7, F-8 reconstructed from §5 Metis findings; F-3, F-4, F-9, F-10 explicitly numbered in §3. F-8 (priv_mode_u) is the root cause that F-9/F-10 surface.

### Deliverables (reference)
- `bosc/Cooperation_RD/RVA23-contribution-to-RVI/intermediate/T243-finding-traceability.md`
- `bosc/Cooperation_RD/RVA23-contribution-to-RVI/intermediate/T243-coverage-audit.md`
- `bosc/Cooperation_RD/RVA23-contribution-to-RVI/intermediate/T243-redundancy-analysis.md`
- `bosc/Cooperation_RD/RVA23-contribution-to-RVI/intermediate/T243-test-coverage-mapping.md`

---

## §5 Tools Cheat Sheet

| Task | Command | Notes |
|------|---------|-------|
| Check if file is gitignored | `git check-ignore -v <path>` | Shows matching .gitignore line |
| Force-add ignored file | `git add -f <path>` | Git keeps tracking after first add |
| Portable sed (cross-platform) | `sed -E 's/pat/repl/g'` | Avoid BRE `\+` on macOS |
| Create missing dirs | `mkdir -p <path>` | Idempotent, no error if exists |
| Shallow clone upstream | `git clone --depth 1 -b <branch> <url>` | Avoids full history pollution |
| Audit all ignored .S files | `git check-ignore -v tests/priv/**/*.S` | Empty output = all tracked |

---

## §6 References

- **Parent skill**: `riscv-skill-pack/SKILL.md`
- **Sibling sub-skills**: `spec-learning.md`, `gap-analysis.md`, `requirement-analysis.md`, `governance.md`
- **T243 source materials**: `bosc/Cooperation_RD/RVA23-contribution-to-RVI/intermediate/T243-*.md`
- **Weekly log reference**: `weekly-logs/weekly-tasks-20260803-20260809.md` (T243.7)
