---
name: riscv-tg-tracker
version: "1.0"
updated: "2026-07-26"
description: >
  RISC-V governance tracking skill for TG/SIG/HC/OpaVote votes and deadlines.
  Activate whenever a task involves tracking RISC-V governance actions,
  OpaVote initiatives, TG charter extensions, HC elections, spec freezes,
  or ratification milestones. This skill enforces systematic vote analysis,
  deadline extraction, KMHv3 impact assessment, and structured recording
  to the RVI_Governance directory. For architecture mapping and tier-1
  source verification, activate the companion skill riscv-tier1-mapping
  alongside this skill.
---

# Skill: riscv-tg-tracker (v1.0)

## When to activate

Activate for any task that:
- Tracks RISC-V Task Group (TG) charter extensions or 1-year approval status.
- Monitors Horizontal Committee (HC) or Special Interest Group (SIG) elections.
- Analyzes OpaVote initiatives for spec freezes, ratifications, or personnel votes.
- Extracts deadlines from OpaVote PDFs, RISC-V wiki announcements, or email notifications.
- Assesses KMHv3 impact of governance actions (blocking vs indirect relevance).
- Records governance analysis to `bosc/Cooperation_RD/RVI_Governance/` directory.
- Produces deadline priority matrices or vote tracking reports for RISC-V governance.

Do **not** activate for purely architectural feature mapping or ISA comparison tasks.
For those, activate **riscv-tier1-mapping** instead or alongside this skill.
Do **not** make voting recommendations. This skill is for research and monitoring only.

---

## 0. Mission

Perform **systematic RISC-V governance tracking** applicable to any TG, SIG, HC,
or OpaVote initiative that may affect KMHv3 delivery or RISC-V ecosystem direction.

Primary outputs:
- Vote type classification with explicit identification markers.
- Deadline extraction with absolute dates and urgency levels (P0-P3).
- KMHv3 impact analysis with direct blocking vs indirect relevance tags.
- Candidate background analysis for personnel elections (research-only, no recommendations).
- Structured recording in `RVI_Governance/` directory with consistent format.
- Cross-reference to `riscv-tier1-mapping` for TG extension status and architecture context.

**Never make voting recommendations. Document analysis, let human decision-makers vote.**

---

## 1. Vote Type Identification

### 1.1 Classification Table

For each governance action encountered, classify using the markers below:

| Vote Type | Identification Markers | Typical Approver | KMHv3 Relevance Pattern |
|-----------|----------------------|------------------|------------------------|
| **TG extension approval** | "1-year extension", "charter renewal", "TG continuation" | TSC / BoD | Affects roadmap planning for TGs with KMHv3 linkage |
| **HC election** | "Chair", "Vice-Chair", "Election", "term" | HC members | Indirect (influences spec direction, not direct blocker) |
| **SIG election** | "Chair", "Vice-Chair", "SIG", "Special Interest Group" | SIG members | Indirect (ecosystem coordination, rarely blocking) |
| **Spec freeze** | "Freeze", "Public Review", "Milestone", "Fast Track" | SOC Infra HC / Priv HC / TSC | High if spec blocks KMHv3 feature (e.g., E-Trace, RHTI, RVA23.1) |
| **Spec ratification** | "Ratification", "Board of Directors", "Ratification-Ready" | TSC -> BoD | High if ratified spec becomes requirement for KMHv3 |
| **Charter update** | "Charter", "Scope change", "Re-charter", "new charter" | TSC | Medium if scope affects KMHv3-relevant features |

### 1.2 Vote Mechanism Identification

| Mechanism | Markers | Typical Use |
|-----------|---------|-------------|
| **Approval vote** | "Approve/Object/Abstain", "may submit empty ballot" | Most technical votes, HC elections |
| **Instant runoff** | "ranked choice", "STV", "preference order" | TG Chair elections with multiple candidates |
| **Simple majority** | "50% +1", "majority of participating" | Freeze/ratification votes |
| **Quorum required** | "quorum", "minimum participation" | Board-level ratification votes |

---

## 2. Deadline Extraction Workflow

### 2.1 Source Hierarchy

1. **Primary**: OpaVote email notification (contains direct link + deadline)
2. **Secondary**: OpaVote PDF ballot (download and parse for detailed deadline text)
3. **Tertiary**: RISC-V wiki / Tech Journal / Jira task (verify deadline accuracy)
4. **Fallback**: RVI_Governance directory existing records (cross-check consistency)

### 2.2 PDF Extraction Method

When OpaVote PDFs contain ballot details not available in email/wiki:

**Method A: pdftotext (preferred)**
```bash
pdftotext -layout opavote-ballot.pdf opavote-ballot.txt
```

**Method B: PyPDF2 (fallback when pdftotext unavailable)**
```python
import PyPDF2

with open("opavote-ballot.pdf", "rb") as f:
    reader = PyPDF2.PdfReader(f)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

# Extract deadline patterns
deadline_patterns = [
    r"Deadline[:\s]+([A-Za-z]+ \d{1,2},? \d{4})",
    r"closes?[:\s]+([A-Za-z]+ \d{1,2},? \d{4})",
    r"due[:\s]+([A-Za-z]+ \d{1,2},? \d{4})",
    r"(\d{4}-\d{2}-\d{2})",
]
```

**Known Limitations**:
- Biography text may truncate in PDF extraction (noted in T191.8b Server SoC II TG)
- Complex layouts (tables, multi-column) may lose structure
- Always verify extracted dates against OpaVote web UI when possible

### 2.3 Deadline Priority Matrix (P0-P3)

After extracting absolute deadlines, assign priority:

| Priority | Criteria | Action Required | Example |
|----------|----------|-----------------|---------|
| **P0** | Due TOMORROW (within 24 hours) | **IMMEDIATE ACTION** | 7/27 vote on 7/26 |
| **P1** | Due this week (2-7 days) | Review today | 7/28 vote on 7/26 |
| **P2** | Due next week (8-14 days) | Plan review window | 7/31 vote on 7/26 |
| **P3** | Due >14 days OR critical path | **CRITICAL - review before vote** | 8/4 vote on 7/26 (RVA23.1) |

**Special Rule**: A P3 deadline can be elevated to P0-equivalent urgency if it is on the
**KMHv3 critical path** (e.g., RVA23.1 freeze blocks profile definition regardless of date distance).

---

## 3. KMHv3 Impact Analysis Workflow

### 3.1 Direct Blocking Assessment

For each governance action:

1. **Does this vote block KMHv3 delivery path?** (Y/N)
2. **Which KMHv3 requirement/deliverable is affected?**
   - Search `bosc/` and `.sisyphus/` for demand numbers (BOSC-xxx, KMH-V3-xxx, 04-02-xx)
   - Cross-reference `riscv-tier1-mapping` skill TG table for known linkages
3. **What is the risk level if missed?**
   - **Critical**: Blocks KMHv3 profile definition or core feature delivery
   - **High**: Delays subsystem or creates compliance gap
   - **Medium**: Affects ecosystem maturity but not direct delivery
   - **Low**: Informational or competitive context only

### 3.2 Gap Analysis (for spec-related votes)

1. **Compare with Arm/x86 analogue** (e.g., Arm CoreSight for E-Trace/RHTI)
2. **Verify spec coverage of KMHv3 requirements**
   - Check KMHv3 requirement documents for explicit spec references
   - Note any mandatory vs optional extension status
3. **Check integration with related specs**
   - Identify upstream/downstream spec dependencies
   - Flag version conflicts or integration gaps

### 3.3 Positive/Negative Factor Identification

| Factor Type | Examples |
|-------------|----------|
| **Positive** | Mature ecosystem, aligns with KMHv3 needs, strong chair candidate, broad industry support |
| **Negative** | Fast timeline (less review time), potential gaps, version immaturity, truncated PDF extraction, candidate background incomplete |

### 3.4 Relevance Tagging

Use consistent tags across all governance tracking outputs:

- **Direct (Blocking)**: Vote outcome directly affects KMHv3 delivery timeline or requirements
- **Strong**: Affects architectural decisions or long-term roadmap (may become blocking)
- **Indirect**: Informative for competitive analysis or ecosystem context (not blocking)

---

## 4. Candidate Background Analysis (Personnel Elections Only)

### 4.1 Extraction Fields

For each candidate in HC/TG/SIG elections:

| Field | Source | Notes |
|-------|--------|-------|
| **Name** | OpaVote PDF / email | Verify spelling |
| **Affiliation** | Candidate statement / biography | Note commercial/academic/government |
| **Position/Title** | Biography | Principal Engineer, Professor, etc. |
| **Experience (years)** | Biography | Total years + domain relevance |
| **Technical Domains** | Biography / statement | Match against KMHv3 needs |
| **RISC-V Contributions** | Biography / GitHub / spec contributions | repos, specs, working groups |
| **Open Source Projects** | Biography | Founder/maintainer status, duration |
| **Candidate Statement** | OpaVote PDF / email | Vision, priorities, collaboration approach |

### 4.2 Analysis Rules

1. **Extract only factual information** from provided sources (PDF, email, wiki).
2. **Do NOT make voting recommendations**. Document candidate attributes neutrally.
3. **Flag incomplete extraction**: If PDF truncation occurs (common with multi-page biographies),
   note "[Candidate info truncated in PDF extraction]" and recommend requesting full biography from RVI if needed.
4. **Assess alignment with KMHv3 needs**:
   - Does candidate's technical domain match KMHv3 subsystem requirements?
   - Does candidate's vision align with KMHv3 ecosystem goals?
   - Note affiliations that may represent commercial ecosystem interests.

---

## 5. Recording to RVI_Governance Directory

### 5.1 File Naming Convention

```
T{task-number}-OpaVote-YYYYMMDD.md
```

Example: `T191-OpaVote-20260726.md`

### 5.2 Report Structure

Use the following structure for all governance tracking reports:

```markdown
# T{xxx} - RVI Governance OpaVote Analysis Report

**Report Date**: YYYY-MM-DD
**Report Period**: YYYY-MM-DD to YYYY-MM-DD
**Reporting Agent**: {Agent Name} (OhMyOpenCode)
**Task Reference**: T{xxx} - {Task description}

---

## Executive Summary

- Total votes: X
- Urgency breakdown: Y this week, Z next week
- KMHv3 blocking: N votes

---

## Part 1: Urgent OpaVote (This Week Deadlines)

### Vote #N: {Title}

| Attribute | Value |
|-----------|-------|
| **Vote Type** | {Personnel Election / Technical Specification} |
| **Deadline** | {Priority flag} **Month DD, YYYY** (or when all votes submitted) |
| **Term** | 1 year (when vote complete -> Month DD, YYYY) |
| **Vote Mechanism** | {Approval vote / Instant runoff} |
| **Approver** | {HC / TSC / BoD} |
| **OpaVote Link** | https://opavote.com/en/vote/XXXXXXXX |

**Candidate** (for personnel elections):
- **Name**: {Name}
- **Affiliation**: {Org}
- **Position**: {Title}
- **Experience**: {Years + domains}

**KMHv3 Relevance**: {Direct (Blocking) / Indirect}
- {Specific impact analysis}

**KMHv3 Impact Analysis**:

**Positive**:
- {Factor 1}
- {Factor 2}

**Concerns**:
- {Factor 1}
- {Factor 2}

**Gap Analysis Needed** (Post-vote or pre-ratification):
- {Gap 1}
- {Gap 2}

---

## Part 2: Next Week OpaVote

[Same structure for less urgent votes]

---

## Part 3: KMHv3 Blocking Summary

### Critical Path Blockers

| Vote | Impact | Blocking | Reason |
|------|--------|----------|--------|
| #N | High/Critical | Direct | {Reason} |

### Indirect Relevance

| Vote | Impact | Blocking | Reason |
|------|--------|----------|--------|
| #N | Medium | Indirect | {Reason} |

---

## Part 4: Deadline Priority Matrix

| Priority | Vote | Deadline | Type | KMHv3 Impact | Action |
|----------|------|----------|------|-------------|--------|
| P0/P1/P2/P3 | #N | MM/DD | {Type} | {Direct/Indirect} | {Action} |

---

## Part 5: Recommendations

### Immediate Actions (Before {date})
1. {Action item}

### This Week's Actions (Before {date})
1. {Action item}

### Critical Action (Before {date})
1. {Action item}

---

## Part 6: Appendices

### Appendix A: OpaVote Links
| Vote | OpaVote Link |
|------|--------------|
| #N | https://opavote.com/en/vote/XXXXXXXX |

### Appendix B: KMHv3 Requirement Cross-Reference
| Vote | KMHv3 Requirement | Status |
|------|-------------------|--------|
| #N | BOSC-xxx / KMH-V3-xxx | {Linked / Not linked} |
```

### 5.3 Example Output Reference

See `bosc/Cooperation_RD/RVI_Governance/T191-OpaVote-20260726.md` for a complete example:
- **6 OpaVote initiatives** analyzed (4 urgent 7/27-7/28, 2 next week 7/31-8/4)
- **4 votes blocking KMHv3**: RVA23.1 (critical path), Server SoC II TG, E-Trace, RHTI
- **Deadline priority matrix**: P0 (TOMORROW 7/27), P1 (7/28), P2 (7/31), P3 (8/4 CRITICAL)
- **KMHv3 impact analysis** with positive factors and concerns for each vote
- **Gap analysis needs** documented for post-freeze and pre-ratification phases

---

## 6. Cross-Reference to riscv-tier1-mapping

### 6.1 When to activate both skills

Activate **riscv-tier1-mapping** alongside this skill when:
- Analyzing TG extension votes that affect architecture features (use tier1-mapping for spec status)
- Performing gap analysis that requires Arm/x86 analogue comparison
- Verifying ratification status of extensions mentioned in OpaVote technical specs
- Checking KMHv3 requirement coverage against ratified extension lists

### 6.2 Data Flow

```
riscv-tg-tracker (this skill)
  -> Identifies vote -> Extracts deadline -> Assesses KMHv3 impact
  -> If spec-related: invoke riscv-tier1-mapping
     -> tier1-mapping provides: spec version, ratification status, Arm/x86 analogue
  -> tg-tracker records combined analysis to RVI_Governance/
```

### 6.3 TG Extension Status Lookup

For TG extension approval votes, cross-reference the `riscv-tier1-mapping` skill
**TG Extension Tracking table** (section 5.4) to determine:
- Current TG status (Draft / Public Review / Ratified)
- Ratification target date
- Chair(s) and affiliation
- Existing KMHv3 linkage (BOSC-xxx references)

**Do NOT duplicate** the TG extension table in this skill. Reference it instead.

---

## 7. Agent Roles (Internal Coordination)

| Role | Owns |
|------|------|
| **Governance Tracker** | TG charter extensions, OpaVote votes, HC elections, spec freezes/ratifications; extracts deadlines, analyzes KMHv3 impact, records in `RVI_Governance/` directory |
| **PDF Extractor** | OpaVote PDF parsing via PyPDF2 or pdftotext; extracts candidate biographies, deadline text, spec details; flags truncation issues |
| **KMHv3 Linkage Analyst** | Cross-references votes with KMHv3 requirements (BOSC-xxx, KMH-V3-xxx); assesses blocking status; performs gap analysis |
| **Deadline Prioritizer** | Assigns P0-P3 priorities; flags critical path elevation; produces deadline matrix |

---

## 8. Interaction Protocol

For every request activating this skill:

1. **Identify scope**: which votes, TGs, HCs, or SIGs are in scope.
2. **Classify vote type** using section 1.1 table.
3. **Extract deadlines** using section 2 workflow (PDF -> PyPDF2/pdftotext -> absolute date -> P0-P3 priority).
4. **Assess KMHv3 impact** using section 3 workflow (blocking assessment -> gap analysis -> positive/negative factors).
5. **For personnel elections**: extract candidate backgrounds using section 4 (research-only, no recommendations).
6. **Cross-reference riscv-tier1-mapping** for spec-related votes (section 6).
7. **Record** using section 5 format to `bosc/Cooperation_RD/RVI_Governance/`.
8. **End with verification checklist**:
   - All deadlines extracted and prioritized?
   - All vote types classified correctly?
   - KMHv3 impact assessed for each vote?
   - Candidate backgrounds extracted (personnel votes only)?
   - Recording file created in RVI_Governance/ directory?
   - Cross-reference to riscv-tier1-mapping made where applicable?

**CRITICAL**: This skill tracks governance actions for **research and monitoring purposes only**.
Do NOT make voting recommendations. Document analysis, let human decision-makers vote.
