---
name: riscv-tier1-mapping
version: "2.3"
updated: "2026-07-26"
description: >
  Tier-1 source, evidence-first RISC-V architecture mapping skill.
  Activate whenever a task involves mapping RISC-V ISA extensions,
  platform specs, or SoC features to Arm / x86 analogues.
  This skill enforces the strict source hierarchy, always-fetch-latest policy,
  and output discipline below before any research or comparison begins.
  For KunMingHu V3/V3R1 product feature queries, activate the companion skill
  kunminghu-v3-feature-list instead of or alongside this skill.
  **v2.3 updates (2026-07-26)**: Added TG extension tracking section + OpaVote tracking workflow.
---

# Skill: riscv-tier1-mapping  (v2.3)

## When to activate

Activate for any task that:
- Maps a RISC-V ISA extension, profile requirement, or SoC feature to an Arm or x86 analogue.
- Verifies a feature's ratification status, platform requirement level (MUST/SHOULD/MAY), or Linux/toolchain support.
- Produces comparison tables, timelines, or checklists for architecture analysis or competitive reviews.
- Answers whether a RISC-V feature closes a specific Arm/x86 gap.
- Drafts or reviews content that must be cited as T1-VERIFIED in any RISC-V architecture document.
- **NEW**: Tracks RISC-V governance actions (TG extensions, OpaVote votes, HC elections, spec freezes/ratifications).

Do **not** activate for purely narrative, creative, or non-architectural tasks.
For KunMingHu V3/V3R1 product-scope questions (feature list, BOSC/MC items, V2R2 delta, schedule), activate **kunminghu-v3-feature-list** as well.

---

## 0. Mission

Perform **tier-1-source, evidence-first RISC-V architecture mapping** applicable to any RISC-V server, client, or embedded platform analysis.

Primary outputs:
- Source-backed feature mappings with explicit T1-VERIFIED / T2-CROSS-CHECKED / UNVERIFIED tags.
- Dimension-by-dimension comparison tables reusable without re-deriving the evidence.
- Timelines and ratification-status flags for any decision horizon.
- **NEW**: TG/SIG/HC/OpaVote governance tracking with deadline and impact analysis.

**Never improvise the architecture. When in doubt, stop and say "UNVERIFIED".**

---

## 1. Source Hierarchy (Hard Requirement)

### 1.1 Tier-1 (Primary) — always fetch the LATEST version

For every tier-1 source listed below, you **MUST fetch or verify the current version** before grounding a claim.
Do not rely on a cached or version-pinned copy if a newer ratification or release may exist.

| Category | Canonical URL / location | What to use |
|---|---|---|
| **RISC-V Ratified Extensions** | https://riscv.atlassian.net/wiki/spaces/HOME/pages/16154769/RISC-V+Technical+Specifications (primary) + https://docs.riscv.org/reference/ (live specs) | Check these pages first for ratification dates and current extension status. The old lf-riscv domain now redirects to riscv.atlassian.net. |
| **RISC-V Technical Specs Archive** | https://riscv.atlassian.net/wiki/spaces/HOME/pages/16154899/RISC-V+Technical+Specifications+Archive | Use for spec PDFs and version history. |
| **RISC-V Unified Database (live specs)** | https://docs.riscv.org/reference/ | Privileged spec, Unprivileged spec, Svpbmt, Ssqosid, Pointer Masking v1.0, Zicfiss/Zicfilp, all ratified extensions. Always link to the specific section (e.g., Priv §3.1.6.5, Unpriv Appendix A, Unpriv §2.1.7). |
| **RVA23 Profile** | https://github.com/riscv/riscv-profiles/blob/main/src/rva23-profile.adoc (repo archived Apr 2026 — read-only) | Mandatory/optional/expansion sets; ratified Oct 2024. Repository archived 2026-04-22; current profile content at docs.riscv.org/reference/. |
| **RISC-V Server Platform Spec** | https://github.com/riscv-non-isa/riscv-server-platform | v1.0 ratified May 2026. Always fetch the latest release tag. |
| **RISC-V Server SoC Spec** | https://github.com/riscv-non-isa/riscv-server-soc | v1.0 ratified Feb 2025. Check for any errata or point releases. |
| **RISC-V BRS** | https://github.com/riscv-non-isa/riscv-brs | v1.0 ratified Aug 2025. |
| **RPMI** | https://github.com/riscv-non-isa/riscv-rpmi | v1.0 ratified Jul 2025. Fetch the latest. |
| **CBQRI** | https://github.com/riscv-non-isa/riscv-cbqri | v1.0 ratified Jun 2024. |
| **RERI** | https://github.com/riscv-non-isa/riscv-ras-eri | v1.0 ratified May 2024. |
| **Self-hosted Trace** | https://github.com/riscv/self-hosted-trace | Draft v0.6.1 Mar 2026; target ratification 2026-2027. Always fetch latest tag. |
| **E-Trace / N-Trace / TCI** | https://github.com/riscv-non-isa/riscv-trace-spec | TCI v1.0 ratified Nov 2024. Check latest for N-Trace errata. |
| **Smmtt / Smmpt** | https://github.com/riscv/riscv-smmtt | v0.49 draft (Jan 2026); ARC freeze ongoing. Fetch latest release. |
| **CoVE / AP-TEE** | https://github.com/riscv-non-isa/riscv-ap-tee | Development draft. Always fetch latest. |
| **Memory Tagging TG (Zimt/Svatag)** | https://github.com/riscv-admin/riscv-memory-tagging | v0.2 draft Sep 2025; spec freeze target 2028. |
| **IME (Integrated Matrix Extension)** | RISC-V Ratified Extensions page above + IME TG GitHub | Ratification plan 2026 H2. Fetch current draft from TG repo. |
| **AME (Attached Matrix Extension)** | https://github.com/riscv/riscv-ame (spec) + https://github.com/riscv-admin/attached-matrix-extension (admin) + UDB `Zvame` | **Draft v0.2** (2026-06-15), ~188 pp. Freeze target end 2026; Public Review 2027-02-07; BoD 2027-04-29. TG RVG-135, Chair: Zhong Su (Alibaba), VC: Derek Hower (Qualcomm), 233 members. **2026-07-01: elementwise instructions added** (PR #11, scope expansion). Software: RACE-org/riscv-ame-{llvm,triton,gem5,matrix-core} (early-stage). Dashboard: https://riscv.github.io/adm-spec-dashboard. |

> **AME vs IME**: AME = attached co-processor with tile registers; IME = integrated into pipeline. Both target ML/HPC. AME tracked as `Zvame` in UDB.
| **Arm ARM (DDI0487)** | https://developer.arm.com/documentation/ddi0487 | Memory model B2.10.2, Device types, MPAM — comparator only. Fetch the latest issue. |
| **Arm Neoverse TRMs** | https://developer.arm.com/documentation (search Neoverse V2/V3 TRM) | Comparator only. |
| **Arm CMN TRMs** | CMN-700: https://developer.arm.com/documentation/102337; CMN S3: https://developer.arm.com/documentation/107858 | Comparator only for NoC/QoS analysis. |
| **Intel/AMD x86 manuals** | Intel SDM, AMD APM (official sites) | Comparator only for TSO, DDIO, RAS, PMU. |
| **Linux mainline** | https://lwn.net (for RFCs and deep analysis) + https://www.cnx-software.com (release summaries) | Kernel version support per RISC-V feature; LWN CBQRI RFC (lwn.net/Articles/1055163), LWN RAS RFC (lwn.net/Articles/1053519). |
| **LLVM / GCC / glibc** | Official upstream repos and changelogs | ABI/codegen evidence for RISC-V features. |

**Always-fetch-latest rule:** Before stating a ratification status, spec version, or Linux support milestone, query the canonical URL above. Do not use a stale version. If the URL is inaccessible, state "COULD NOT VERIFY — last known: [version/date]" and flag it for human review.

### 1.2 Tier-2 (Cross-check) — corroborate only, never contradict tier-1

- Reputable vendor blogs: Arm, SiFive, Cadence, Synopsys, AMD, NVIDIA …
- Conference papers: XiangShan Summit Europe 2024, CARRV, LPC 2025 QoS slides (lpc.events/…/RISC-V%20QoS%20LPC%202025.pdf), RISC-V Summit …
- High-quality third-party: Chips and Cheese, kernel deep dives, Canonical RISC-V blog …

Rules:
- Never contradict tier-1; if tier-2 disagrees, state it and side with tier-1.
- Tag as **T2-CROSS-CHECKED** and cite the specific blog/paper.
- May suggest implementation strategies — mark them **INTERPRETIVE**.

### 1.3 Tier-3 (Disallowed for ground truth)

Do not use: unvetted forums, unsourced GitHub gists, marketing slides, rumors, leaks.
If unavoidable, label "UNVERIFIED" and explain why no tier-1/tier-2 source was available.

---

## 2. Canonical Mapping Dimensions

Apply all six dimensions for every comparison. Skip none.

| # | Dimension | Key questions |
|---|---|---|
| 1 | Ratification & maturity | Ratified? Draft? Charter-only? Profile status (RVA23 mandatory/optional/expansion)? Platform spec (Server Platform / Server SoC / BRS / RPMI) status? What is the ETA? |
| 2 | ISA semantics | Instruction/CSR level behavior? Interaction with RVWMO, RVTSO, IO ordering channels (0/1/N), PMAs (Priv §3.1.6)? |
| 3 | Platform requirements | MUST / SHOULD / MAY / guidelines-only in Server Platform / Server SoC specs? Quantitative constraints (HPM counts, RCID/MCID ranges, timer precision, interrupt file counts, VLEN floors)? |
| 4 | Software evidence | Linux version? Role (KVM, IOMMU, resctrl, APEI, PMEM, CFI)? Selftests, perf events, kconfig flags? Toolchain (LLVM/GCC/glibc)? |
| 5 | Competitive anchor | Arm analogue (version-tagged), x86 analogue, CXL/UCIe if relevant. Is RISC-V stronger / weaker / just different? |
| 6 | Deployment intent | Server / client / embedded? Agentic AI / matrix / confidential computing / PMEM? Near-term / mid-term / long-term horizon? |

---

## 3. Required Behaviors by Theme

### 3.1 Memory Model and IO Ordering
- **Ground truth**: Priv spec §3.1.6.5 (PMAs, IO ordering channels), Unpriv spec Appendix A (RVWMO PPO rules 3–5), Unpriv §2.1.7 (FENCE IO bits), Svpbmt v1.0.
- **Channel semantics** (Priv §3.1.6.5): Channel 0 = point-to-point strong ordering within one IO region only; Channel 1 = global strong ordering across all IO regions (equivalent to FENCE io,io before and after); Channel N ≥ 2 = grouped strong ordering across same-channel regions.
- **Map to Arm Device types** (DDI0487 B2.10.2): nGnRnE (no-Gather, no-Reorder, no-EarlyWriteAck) ↔ Channel 1; nGnRE ↔ Channel 0 with endpoint ACK required; nGRE ↔ relaxed-ordered IO with barriers; GRE ↔ relaxed IO RVWMO. State Gathering, Reordering, and Early Write Ack dimensions explicitly.
- For Svpbmt PBMT=IO: state interaction with IO channel 0 strong ordering.
- **PCIe caveat**: RVWMO ordering may not extend beyond the RISC-V core boundary onto PCIe; platform-specific rules apply (Unpriv Appendix A platform-specific boundary note).
- Do not weaken or strengthen ordering guarantees beyond spec language. Tag: T1-VERIFIED with the specific section URL.

### 3.2 QoS: MPAM vs Ssqosid + CBQRI
- **Core evidence (T1)**: Ssqosid v1.0 (ISA, Jun 2024), CBQRI v1.0 (non-ISA, Jun 2024), ACPI RQSC, Server Platform QoS requirements, LWN CBQRI RFC Jan 2026 (lwn.net/Articles/1055163).
- **Arm comparator**: MPAM v1.1 (ARM Neoverse V2 TRM §A.13 — up to 511 PARTID, 32 PMG, per-EL CSR, resctrl 10 partitions).
- Produce a dimension-by-dimension table: ID spaces (Arm PARTID/PMG vs RISC-V RCID/MCID), bandwidth accounting, throttling, cache allocation, per-EL vs per-mode, hypervisor VRCID gap.
- Distinguish: ISA-visible QoS CSR (Ssqosid srmcfg) | platform-level spec requirements | OS/user-space control via Linux resctrl RFC.
- Flag: Linux resctrl RFC patch series Jan 2026; estimated merge Linux 6.15–6.16 (T1-VERIFIED: LWN).

### 3.3 Security, CFI, and Memory Tagging
- **RISC-V anchors (T1)**:
  - CFI: Zicfiss (shadow stack, Jun 2024, RVA23 Expansion Optional), Zicfilp (landing pad, Jun 2024, RVA23 Expansion Optional).
  - Pointer Masking: Zpm family (RVA23 Mandatory) — tag bits in pointer, hardware ignores during address resolution; does NOT provide tag mismatch detection by itself. Fetch Pointer Masking v1.0 spec (docs.riscv.org/reference/isa/priv/zpm.html) for latest.
  - Memory Tagging: Zimt/Svatag, charter May 2024, v0.2 draft Sep 2025, spec freeze 2028. Pointer Masking does not substitute for full hardware memory tagging.
  - CoVE / AP-TEE: riscv-ap-tee dev draft. Smmtt v0.49 draft (Jan 2026). Fetch latest.
- **Arm comparators**: PAC+BTI (CFI) vs Zicfiss/Zicfilp; MTE3 (ARM Neoverse V2, FEAT_MTE3, 4-bit tags, 16 B granules, tag mismatch → Data Abort/SError) vs Pointer Masking + Zimt TG.
- **x86**: CET shadow stack vs Zicfiss; ENDBRANCH vs Zicfilp.
- Separate: mandatory in RVA23 profile | optional/expansion | future horizon.
- State ratified vs draft status for every cited RISC-V item.

### 3.4 Trace, PMU, and Observability
- **RISC-V baseline (T1)**:
  - Self-hosted Trace: Smstrc/Ssamb, draft v0.6.1 Mar 2026, target ratification 2026–2027. Fetch latest from github.com/riscv/self-hosted-trace.
  - E-Trace 2.0 (Jun 2025), N-Trace 1.0 (Nov 2024): github.com/riscv-non-isa/riscv-trace-spec.
  - TCI v1.0 (Nov 2024), Ssctr/Smctr CTR (Nov 2024, RVA23 Optional/ARC Aug 2025). Sdtrig / Sdext Debug Spec 1.0 (ratified Feb 2025).
  - Server SoC HPM requirements: SPM010–060. Per-hart PMU: Zicntr/Zihpm CSRs + SBI PMU extension.
- **Arm comparators**: ETM / N-Trace / BRBE (ISA) / CMN DTM/DTC (fabric) — version-tag each. CMN-700 vs CMN-S3 PMU differences.
- **x86**: Intel Processor Trace, AMD uProf, Uncore PMU.
- Emphasize: per-hart vs fabric/NoC trace; on-die vs off-die; required vs optional in Server Platform/SoC spec.
- SoC design pattern: E-Trace encoder per-hart → ATB/AXI-Stream → Trace sink DRAM; NoC DTM/DTC trace.

### 3.5 Confidential Computing and CoVE
- **RISC-V anchors (T1)**:
  - CoVE (riscv-ap-tee) dev draft: TSM/TVM model, Memory Integrity Engine (replay/splicing protection via AES-GCM / HMAC-SHA256 on DDR controller).
  - Smmtt v0.49 / Smmpt: supervisor domains, memory protection table, ARC freeze ongoing. Fetch latest release.
  - Server SoC SEC030 (DRAM encryption), SEC020 (PCIe IDE), COVI interrupt isolation.
- **Competitive map**:
  - Intel TDX: SEAM/TSM role, SEPT page table, TDCALL/SEAMCALL ISA.
  - AMD SEV-SNP: RMP (Reverse Map Table), SNP page validation, PSP secure processor.
  - Arm CCA: RMM/Realm, GPT (Granule Protection Table), S-EL2.
- Map axes: trust anchor, MPT/page-table structure, interrupt/IO isolation mechanism.
- State ratified vs draft for each RISC-V item.

### 3.6 Matrix / Vector / Crypto Extensions
- **RISC-V (T1)**:
  - RVV 1.0: RVA23 Mandatory, VLEN ≥ 128. Fetch latest VLEN floor for any specific platform profile.
  - IME: Ratification plan 2026 H2 (Aug 27, 2026 target). Fetch TG repo for current draft.
  - Vector crypto: Zvkn (Jun 2023, RVA23 Mandatory), Zvkb (Mandatory), Zvbc (Development Option), Zvkng/Zvksg (post-RVA23).
  - BF16: ZvfbfminZvfbfwma (Jun 2024, RVA23 Expansion Options).
- **Arm**: SVE2 (Neoverse V2 — 4× 128-bit pipes, FEAT_SVEAES/SHA3/SM4); SME2 (matrix tiles).
- **x86**: AVX-512 (Intel Xeon); AMX (Intel, matrix tiles, 2D register).
- Map: element types/precisions (fp64/fp32/bf16/fp16/fp8/int8), register organization (vector length vs matrix tiles vs LMUL), profile integration level.

### 3.7 MMIO Outstanding and IO Ordering
- Outstanding MMIO loads/stores: RISC-V does not define a per-channel outstanding count the way Arm CMN tracks OT. State this gap explicitly for any IO coherency analysis.
- When mapping RISC-V IO channel N to Arm Device types, note that Arm nGnRnE maps closest to Channel 1 (global strong ordering), but does not have an explicit per-region "channel number" concept.
- The Svpbmt PBMT=NC (non-cacheable, non-idempotent) interaction with FENCE and outstanding loads is architecturally distinct from PBMT=IO. State this clearly.
- Reference: Priv §3.1.6.5, Unpriv Appendix A, DDI0487 B2.10.2.

---

## 4. Output Requirements

1. **Tag every factual claim** as:
   - `T1-VERIFIED <spec name + section or URL>`
   - `T2-CROSS-CHECKED <source name + URL>`
   - `UNVERIFIED` (explain why no tier-1/tier-2 source was available)

2. **Always-fetch-latest**: Before finalizing any claim about ratification status, platform spec version, or Linux support, verify against the canonical URL in §1.1. If you detect a version newer than what was previously cited, flag it as **SPEC-UPDATE-ALERT**.

3. **Produce explicit mapping tables** per theme. Minimum columns:
   `Feature | RISC-V (spec + status) | Arm/x86 analogue | Platform requirement | Software evidence | Tag`

4. **Include timelines with status flags**:
   - `RATIFIED <date>` / `PUBLIC REVIEW <date>` / `DRAFT <date>` / `RATIFICATION PLAN <target date>`

5. **Scope every statement** to a named profile (e.g., RVA23) and platform spec version (e.g., Server Platform v1.0, Server SoC v1.0). Never say "all RISC-V".

6. **Separate the concern** per claim:
   - Programmer-visible semantics
   - Microarchitectural implementation pattern
   - Platform integrator requirement (MUST/SHOULD/MAY)
   - OS / toolchain support expectation

7. **End with a verification checklist** the reader can use to validate the mapping, including:
    - Which spec URLs to re-check before the next milestone review.
    - Any open architectural gaps or unresolved questions identified during the analysis.

---

## 5.4 TG Extension Tracking

For tracking RISC-V Task Group (TG) charter extensions and 1-year approval status:

### 5.4.1 Tracked TGs (11 approved for 1-year extension as of 2026-07-26)

| # | TG | Status | Ratification Target | Chair(s) | KMHv3 Linkage |
|---|----|--------|---------------------|----------|--------------|
| 1 | **IOPMP** | 🟠 Draft / ARC Review (spec v0.8.2) | Undetermined (ARC review, ≥2027) | Paul Ku (Andes) / Channing Tang (NVIDIA) | 🔴 **BOSC-616** (F21 gap-analysis), KMH-V3-616.8, 04-02-08 §C-5 |
| 2 | **Fast Interrupts** | 🟢 AIA Ratified (2023-06); 🟠 CLIC developing | AIA ✅ ratified; CLIC TBD | TG election 2026-06-02 | 🔴 **BOSC-602 / BOSC-617 / BOSC-652** (IMSIC+APLIC), 04-02-00 |
| 3 | **AME** | 🟠 Draft (188 pages, migrating to Unified DB) | Public Review 2027-02-07; BoD 2027-04-29 | Zhong Su (Alibaba) / Derek Hower (Qualcomm) | 🔴 **KMHv3 feature #26** (M4/01 reserved), req row 69-70, **T190.1** |
| 4 | **Packed SIMD (P extension)** | 🟠 Draft / long-term development (re-scoped) | Undetermined (≥2027) | Rich Fuhler (2026 election in progress) | 🟡 Weak (no direct KMHv3 demand reference; RVV covers vector path) |
| 5 | **SPMP (S-mode PMP)** | 🟢 Public Review 2026-05-22 → 2026-06-21 | 2026 H2 (post-PR TSC→BoD) | Bicheng Yang / Sandro Pinto | 🟡 Indirect (RVS-921 ARC review; RVA_020 Smepmp ratified) |
| 6 | **SmMTT (Supervisor Domain Isolation)** | 🟠 Draft v0.49 (ARC review / Freeze phase) | No commitment (no public date) | TG RVG-65 (chartered 2023-04) | 🟠→🔴 **Strong relevance** (BOSC-603/615 confidential compute; overlaps with T191.2c CoVE) |
| 7 | **CHERI (Capability Hardware)** | 🟠 Draft v0.9.8 (ARC review) | Q3 2026 (CHERI Blossoms 2026, optimistic) | Alex Richardson (Google) / Simon Moore (Cambridge) co-chair; Tariq Kurd (Codasip) spec lead | 🟡 Indirect (KMHv3 listed as "alternative", Codasip X730 commercialized; not in RVA23/Server Platform) |
| 8 | **CoVE (AP-TEE)** | 🟠 Development (spec unratified, "Assume everything can change") | Undetermined (spec still Draft, unFrozen) | **Ravi Sahita (Rivos)** + **Guerney Hunt** (co-chair) | 🟡 Indirect (V3 selects CoVE path, BOSC-615) |
| 9 | **Security Model** | 🟠 Development (v0.5 in ARC review, unFrozen) | Undetermined (ARC review, ≥2027) | **Andrew Dellow** (reports to Security HC) | 🟡 Indirect (security domain framework baseline, non-normative) |
| 10 | **CoVE-IO** | 🟠 Internal Review (v0.3.0, 2026-02-18, unFrozen) | Undetermined (pre-ARC, ≥2027 H2) | Public results unclear (pending charter/election) | 🟡 Indirect (KMH-V3-616.9 R3 candidate) |
| 11 | **PQC (Post-Quantum Cryptography)** | 🟠 In Progress (Keccak instructions in development, has Ratification Plan) | Has plan, milestones per wiki | **Markku-Juhani Saarinen** (chair) / **Nicolas Brunie** (vice-chair) | 🟡 Indirect (most distant, no direct KMHv3 demand) |

**Legend**:
- 🔴 **Direct relevance**: Blocks or directly enables KMHv3 delivery path
- 🟠 **Strong relevance**: Affects KMHv3 architectural decisions or long-term roadmap
- 🟡 **Indirect relevance**: Informative for competitive analysis or future evolution

### 5.4.2 Research Sources (T191.2a/b/c notepads)

- `.sisyphus/notepads/T191/research-T191.2a.md` (IOPMP, Fast Interrupts, AME)
- `.sisyphus/notepads/T191/research-T191.2b.md` (Packed SIMD, SPMP, SmMTT, CHERI)
- `.sisyphus/notepads/T191/research-T191.2c.md` (CoVE, Security Model, CoVE-IO, PQC)

**Validation Methodology**:
1. For each TG: fetch latest spec version from canonical GitHub repo
2. Extract: Status, latest version, ratification target, chair(s)
3. Cross-reference KMHv3 requirements (grep `bosc/` and `.sisyphus/` for demand numbers)
4. Tag relevance level: 🔴 Direct blocking / 🟠 Strong / 🟡 Indirect

---

## 5.5 OpaVote Tracking Workflow

For systematic tracking of RISC-V governance actions on OpaVote:

### 5.5.1 Vote Type Identification

| Vote Type | Identification Markers | Typical Approver | KMHv3 Relevance Pattern |
|-----------|----------------------|------------------|------------------------|
| **TG extension approval** | "1-year extension", "charter renewal" | TSC / BoD | Affects roadmap planning for TGs with KMHv3 linkage |
| **HC election** | "Chair", "Vice-Chair", "Election" | HC members | Indirect (influences spec direction, not direct blocker) |
| **Spec freeze** | "Freeze", "Public Review", "Milestone" | SOC Infra HC / Priv HC | High if spec blocks KMHv3 feature (e.g., E-Trace, RHTI) |
| **Spec ratification** | "Ratification", "Board of Directors", "Ratification-Ready" | TSC → BoD | High if ratified spec becomes requirement for KMHv3 |
| **Charter update** | "Charter", "Scope change", "Re-charter" | TSC | Medium if scope affects KMHv3-relevant features |

### 5.5.2 Deadline Extraction Process

1. **Source**: RISC-V wiki / OpaVote email / RVI_Governance directory
2. **Extract**:
   - Deadline date (absolute or relative to "when all votes submitted")
   - Urgency level: 🔴 This week / 🟡 Next week / 🟢 Future
   - Vote type (personnel vs technical)
   - Approver body (HC, TSC, BoD)
3. **Prioritize**:
   - 🔴 Urgent (7/27-7/28): Requires immediate action before missing deadline
   - 🟡 Next week (7/31-8/4): Plan review window
   - 🟢 Future: Track for upcoming milestone

### 5.5.3 KMHv3 Impact Analysis Workflow

For each OpaVote:

1. **Direct Blocking Assessment**:
   - Does this vote block KMHv3 delivery path? (Y/N)
   - Which KMHv3 requirement/deliverable is affected?
   - What is the risk level if missed? (Critical / High / Medium / Low)

2. **Gap Analysis** (for spec-related votes):
   - Compare with Arm/x86 analogue (e.g., Arm CoreSight for E-Trace/RHTI)
   - Verify spec coverage of KMHv3 requirements
   - Check integration with related specs

3. **Positive/Negative Factor Identification**:
   - Positive: Mature ecosystem, aligns with KMHv3 needs
   - Negative: Fast timeline (less review time), potential gaps, version immaturity

4. **Output**: Record in `bosc/Cooperation_RD/RVI_Governance/` directory with:
   - Vote metadata (type, deadline, approver, OpaVote link)
   - KMHv3 relevance tag (🔴 Direct / 🟡 Indirect)
   - Impact analysis (positive/negative factors)
   - Gap analysis needs (post-vote or pre-ratification)

### 5.5.4 Recording Format

**File naming**: `T191-OpaVote-YYYYMMDD.md` (per analysis cycle)

**Report structure** (example: `bosc/Cooperation_RD/RVI_Governance/T191-OpaVote-20260726.md`):

```markdown
## Executive Summary
- Total votes: X
- Urgency breakdown: Y this week, Z next week
- KMHv3 blocking: N votes

## Part 1: Urgent OpaVote (This Week Deadlines)
Vote #N: [Title]
| Attribute | Value |
|-----------|-------|
| Vote Type | Personnel Election / Technical Spec |
| Deadline | 🔴 July XX, 2026 |
| Approver | HC / TSC / BoD |
| OpaVote Link | https://opavote.com/en/vote/XXXXXXXX |

KMHv3 Relevance: 🔴 Direct / 🟡 Indirect
- [Specific KMHv3 impact analysis]

## Part 2: Next Week OpaVote
[Similar structure for less urgent votes]
```

**Example Output**: See `T191.8c` output in `bosc/Cooperation_RD/RVI_Governance/T191-OpaVote-20260726.md` (6 OpaVote analysis covering 4 urgent + 2 next-week votes; 4 blocking KMHv3: RVA23.1, Server SoC II TG, E-Trace, RHTI)

**CRITICAL**: This skill tracks governance actions for **research and monitoring purposes only**. Do NOT make voting recommendations. Document analysis, let human decision-makers vote.

---

## 6. Agent Roles (Internal Coordination)

| Role | Owns |
|---|---|
| ISA & Memory Model Lawyer | Priv/Unpriv spec, PMAs, RVWMO, IO channels 0/1/N, Svpbmt, FENCE semantics; prevents over-claims; enforces always-fetch-latest for ISA specs |
| Platform & QoS Architect | Server Platform Spec, Server SoC Spec, BRS, RPMI, Ssqosid+CBQRI+RQSC, AIA, Arm MPAM/CMN, x86 Uncore; version-checks platform spec before citing requirements |
| Security & Confidential Computing Analyst | Zicfiss/Zicfilp, Pointer Masking Zpm, Zimt/Svatag, CoVE/Smmtt, DRAM encryption, PCIe IDE, RoT |
| Observability & Software Integrator | Linux kernel version evidence, perf/PMU/trace, IOMMU/resctrl/APEI, toolchain support; checks LWN for latest RFC merge status |
| Competitive Systems Analyst | Arm Neoverse V2/V3, Intel Xeon SPR/GNR, AMD EPYC Genoa/Turin, NVIDIA Grace, CXL/UCIe-based systems, RISC-V vendor SoCs (SiFive P870, Ventana Veyron C1, XiangShan) — always tier-1 grounded, version-tagged |
| **Governance Tracker** | **NEW**: TG charter extensions, OpaVote votes, HC elections, spec freezes/ratifications; extracts deadlines, analyzes KMHv3 impact, records in `RVI_Governance/` directory |

---

## 7. Interaction Protocol

For every request activating this skill:

1. **Identify scope**: which features, specs, and profiles are in scope.
2. **Fetch-or-check-latest**: for each tier-1 source you will cite, verify the current version against §1.1 canonical URLs before proceeding.
3. **Map along all six canonical dimensions** (§2).
4. Use tables and dense paragraphs. Avoid narrative bloat.
5. **State explicitly**:
   - Where RISC-V is stronger, weaker, or different vs Arm/x86.
   - Where ecosystem/software gaps are the bottleneck vs ISA/platform gaps.
6. **Emit SPEC-UPDATE-ALERT** if you discover a spec version newer than what was previously cited.
7. **End with the verification checklist** including spec URLs to re-check and open architectural gaps.

If a request requires speculation beyond tier-1 plus disciplined tier-2 cross-checks — **stop, explain the limitation, and do not guess**.
