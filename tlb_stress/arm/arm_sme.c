/*
 * arm/arm_sme.c - Arm SME2 / Streaming SVE vector TLB-stress test.
 *
 * TLB-miss strategy
 * ─────────────────
 * A single SVE *gather load* (ld1d) or *scatter store* (st1d) is issued
 * in Streaming SVE mode.  Each element's address is:
 *
 *   addr_i = buf + page_offsets[i]          (byte offset into test_buf)
 *
 * where page_offsets[i] points into a distinct 4 KiB page chosen at
 * random by main.c.  With SVL=2048 bits, 32 × 64-bit elements are
 * processed by one instruction, causing up to 32 independent TLB lookups
 * in a single pipeline cycle.
 *
 * Streaming SVE mode (PSTATE.SM=1) is entered with SMSTART SM and exited
 * with SMSTOP SM.  The SMCR_EL1.LEN field was set to maximum in startup.S
 * so we get the widest available vector.
 *
 * Instruction encodings used for SME mnemonics not yet in GCC 13's assembler:
 *   SMSTART SM  = 0xD503437F  (MSR SVCR, #1  – set SM bit)
 *   SMSTOP  SM  = 0xD503427F  (MSR SVCR, #2  – clear SM bit)
 *   RDSVL Xd,#1 = 0x04BF5820  (read streaming SVE VL in bytes into X0)
 */

#include "../common.h"

void run_vector_test(const tlb_config_t    *cfg,
                     volatile uint8_t      *buf,
                     const uint64_t        *page_offsets,
                     unsigned               n_elems)
{
    /* n_elems is bounded by MAX_PAGES_TESTED; ptrue activates all SVL lanes */
    (void)n_elems;

    /*
     * ── Enter Streaming SVE mode ─────────────────────────────────────────
     * SMSTART SM (0xD503437F) sets PSTATE.SM=1.  SVE registers (Z/P) become
     * streaming registers with width = SVL.  SMCR_EL1 was configured in
     * startup.S to request the maximum hardware SVL.
     */
    asm volatile(".inst 0xD503437F" ::: "memory");  /* SMSTART SM */

    if (cfg->do_store) {
        /*
         * ── THE TLB-stress instruction: SVE indexed scatter store ─────────
         *
         * Instruction form:
         *   st1d  { z0.d }, p0, [x_base, z1.d]
         *
         * Operands:
         *   { z0.d }   – data to store; 64-bit element view of SVE reg z0
         *   p0         – governing predicate; set all-true by "ptrue p0.d",
         *                meaning every lane [0 .. SVL/64 − 1] is active
         *   x_base     – scalar base address (= buf argument)
         *   z1.d       – index vector; z1.d[i] holds a 64-bit byte offset
         *
         * Effective address of element i:
         *   EA_i = x_base + z1.d[i]   (SVE "base + vector-of-offsets" form)
         *
         * Why this causes many TLB misses
         * ────────────────────────────────
         * z1.d is loaded from page_offsets[], which was populated by main.c
         * with randomly-chosen, distinct 4 KiB-aligned byte offsets.  Because
         * each EA_i sits in a different virtual page, the CPU/MMU must perform
         * a separate TLB lookup (and potentially a page-table walk) for every
         * active lane.  With SVL = 2048 bits there are 32 active 64-bit lanes,
         * so this single instruction can trigger up to 32 TLB misses.
         *
         * Contrast with a contiguous store:
         *   st1d { z0.d }, p0, [x_base]        ← lane i at x_base + i×8
         * All 32 lanes would lie in a 256-byte window (well under one 4 KiB
         * page), so a contiguous store causes at most ONE TLB miss.
         *
         * The gather/scatter form is the only SVE addressing mode that lets a
         * single instruction span an arbitrary set of virtual pages.
         */
        asm volatile(
            /* All-true predicate for 64-bit elements */
            "ptrue  p0.d                          \n\t"
            /* Contiguous load: read page_offsets[] (all in one page) into z1 */
            "ld1d   { z1.d }, p0/z, [%1]         \n\t"
            /* Fill store data with a recognisable canary value */
            "dup    z0.d, #0x5A                   \n\t"
            /* ── ONE scatter store: EA_i = buf + z1.d[i] ─────────────────── */
            "st1d   { z0.d }, p0, [%0, z1.d]     \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "p0", "z0", "z1", "memory"
        );
    } else {
        /*
         * ── THE TLB-stress instruction: SVE indexed gather load ───────────
         *
         * Instruction form:
         *   ld1d  { z0.d }, p0/z, [x_base, z1.d]
         *
         * Operands:
         *   { z0.d }   – destination; 64-bit element view of SVE reg z0
         *   p0/z       – governing predicate (all-true); "/z" means zeroing:
         *                inactive lanes are written to 0 rather than kept
         *   x_base     – scalar base address (= buf argument)
         *   z1.d       – index vector; z1.d[i] is a 64-bit byte offset
         *
         * Effective address of element i:
         *   EA_i = x_base + z1.d[i]   (SVE "base + vector-of-offsets" form)
         *
         * Why this causes many TLB misses
         * ────────────────────────────────
         * z1.d holds page_offsets[0..n-1], each pointing into a randomly
         * chosen distinct 4 KiB page within test_buf.  The CPU must translate
         * every EA_i independently; because none of them share a page, all n
         * translations miss the TLB (which was just capacity-evicted by the
         * sweep in main.c).  With SVL = 2048 bits → 32 lanes → up to 32
         * independent TLB misses from this one instruction.
         *
         * Contrast with the two non-indexed SVE load forms:
         *   ld1d { z0.d }, p0/z, [x0]       contiguous: EA_i = x0 + i×8
         *   ld1d { z0.d }, p0/z, [x0, x1]   scalar+reg: EA_i = x0+x1 + i×8
         * Both keep all lanes within a small window → ≤ 1 TLB miss total.
         *
         * The result in z0 is intentionally discarded; only the address
         * translation side-effects (TLB traffic and page-walk cost) matter.
         */
        asm volatile(
            /* All-true predicate for 64-bit elements */
            "ptrue  p0.d                          \n\t"
            /* Contiguous load: read page_offsets[] (all in one page) into z1 */
            "ld1d   { z1.d }, p0/z, [%1]         \n\t"
            /* ── ONE gather load: EA_i = buf + z1.d[i] ───────────────────── */
            "ld1d   { z0.d }, p0/z, [%0, z1.d]  \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "p0", "z0", "z1", "memory"
        );
    }

    /*
     * ── Exit Streaming SVE mode ──────────────────────────────────────────
     * SMSTOP SM (0xD503427F) restores PSTATE.SM=0; Z/P registers are zeroed
     * on exit per the SME specification to avoid information leakage.
     */
    asm volatile(".inst 0xD503427F" ::: "memory");  /* SMSTOP SM */
}
