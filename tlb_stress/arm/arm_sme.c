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
         * ── THE TLB-stress instruction: scatter store ─────────────────────
         *
         *   st1d { z0.d }, p0, [x_base, z1.d]
         *
         * z0.d  = data (filled with a canary so the write is valid)
         * p0    = all-true predicate  (ptrue p0.d)
         * x_base = buf base address
         * z1.d  = byte offsets loaded from page_offsets[]
         *
         * Each element i writes buf[page_offsets[i]], touching a different
         * 4 KiB page → up to SVL/64 TLB misses from one instruction.
         */
        asm volatile(
            /* All-true predicate for 64-bit elements */
            "ptrue  p0.d                          \n\t"
            /* Load offset vector from page_offsets[] */
            "ld1d   { z1.d }, p0/z, [%1]         \n\t"
            /* Fill store data with a recognisable canary value */
            "dup    z0.d, #0x5A                   \n\t"
            /* ── ONE scatter store (the TLB-stress instruction) ── */
            "st1d   { z0.d }, p0, [%0, z1.d]     \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "p0", "z0", "z1", "memory"
        );
    } else {
        /*
         * ── THE TLB-stress instruction: gather load ───────────────────────
         *
         *   ld1d { z0.d }, p0/z, [x_base, z1.d]
         *
         * z0.d  = destination (result discarded; only TLB traffic matters)
         * p0    = all-true predicate
         * x_base = buf base address
         * z1.d  = byte offsets loaded from page_offsets[]
         *
         * Each element i reads buf[page_offsets[i]], touching a different
         * 4 KiB page → up to SVL/64 TLB misses from one instruction.
         */
        asm volatile(
            /* All-true predicate for 64-bit elements */
            "ptrue  p0.d                          \n\t"
            /* Load offset vector from page_offsets[] */
            "ld1d   { z1.d }, p0/z, [%1]         \n\t"
            /* ── ONE gather load (the TLB-stress instruction) ── */
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
