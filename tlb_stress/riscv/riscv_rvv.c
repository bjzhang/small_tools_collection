/*
 * riscv/riscv_rvv.c - RISC-V RVV 1.0 vector TLB-stress test.
 *
 * TLB-miss strategy
 * ─────────────────
 * A single RVV *indexed unordered load* (vloxei64.v) or
 * *indexed unordered store* (vsoxei64.v) is issued with the maximum
 * vector length supported by the hart.  Each element's effective address is:
 *
 *   effective_address_i = buf + index_vec[i]     (64-bit byte offset)
 *
 * where index_vec[i] = page_offsets[i] points into a distinct 4 KiB page
 * chosen at random by main.c.  With VLEN=256 and LMUL=m8, 32 elements
 * are processed by one instruction, causing up to 32 TLB misses.
 *
 * LMUL=m8 (8-register group) is used to maximise active elements:
 *   VLMAX = floor(VLEN × LMUL / SEW) = floor(VLEN × 8 / 64) = VLEN/8
 *
 * ── Understanding the mnemonic: vloxei64.v ─────────────────────────────────
 *
 *  v  l  ox  ei64  .v
 *  │  │   │    │    └─ No mask operand (all active elements from VL)
 *  │  │   │    └────── Element-Indexed width = 64 bits: each entry in the
 *  │  │   │            index vector register vs2 is a 64-bit byte offset.
 *  │  │   │            Using 64-bit indices allows full 64-bit address space
 *  │  │   │            coverage (required for >4 GiB buffers).
 *  │  │   └─────────── Offset-indexed ("ox"): per-element address computed as
 *  │  │                  EA_i = rs1 + vs2[i]
 *  │  │                This is the "gather" addressing mode.
 *  │  └─────────────── Load (l); the matching store is vsoxei64.v
 *  └────────────────── Vector instruction prefix
 *
 *  Full prototype:  vloxei64.v  vd, (rs1), vs2
 *    vd   – destination vector register group (LMUL register groups wide)
 *    rs1  – scalar base address register
 *    vs2  – index vector register group (holds 64-bit byte offsets)
 *
 * ── "ox" vs "ux" — ordering variants ──────────────────────────────────────
 *
 * RVV 1.0 offers two indexed load/store variants:
 *   vloxei64.v  ("ordered indexed")   – accesses appear in element order
 *   vluxei64.v  ("unordered indexed") – hardware may reorder accesses
 *
 * Both compute EA_i = rs1 + vs2[i] with unsigned 64-bit offsets.  The
 * distinction matters for stores with aliasing; for this TLB-stress test
 * (where every element targets a distinct page) both are equivalent.
 * vloxei64.v is used because all compilers support it.
 *
 * ── Contrast with non-indexed RVV load variants ────────────────────────────
 *
 * | Mnemonic            | Address of element i           | TLB pressure    |
 * |---------------------|--------------------------------|-----------------|
 * | vle64.v   vd,(rs1)  | rs1 + i × 8  (unit stride)    | ≤ 1 miss/line   |
 * | vlse64.v  vd,(rs1),rs2 | rs1 + i×rs2 (fixed stride) | 1 miss/stride   |
 * | vloxei64.v vd,(rs1),vs2 | rs1 + vs2[i] (arbitrary)  | up to VL misses |
 *
 * Only the indexed form enables each element to live on its own page,
 * causing the CPU to perform VL independent TLB lookups per instruction.
 *
 * ── Register allocation under LMUL=m8 ─────────────────────────────────────
 *
 *   v0..v7   – data group  (gather load destination / scatter store source)
 *   v8..v15  – index group (64-bit byte offsets loaded from page_offsets[])
 *
 * LMUL=m8 means each "register" is actually 8 physical registers wide.
 * v0 refers to v0..v7; v8 refers to v8..v15.  This doubles the number of
 * active elements vs LMUL=m4 for the same VLEN.
 *
 * Note: EEW of the *index* group (vs2) must be 64-bit (ei64) regardless of
 * the data EEW, so that offsets can span the full virtual address space.
 */

#include "../common.h"

void run_vector_test(const tlb_config_t    *cfg,
                     volatile uint8_t      *buf,
                     const uint64_t        *page_offsets,
                     unsigned               n_elems)
{
    /*
     * Set the application vector type:
     *   SEW  = e64  (64-bit elements; matches the 64-bit page_offsets)
     *   LMUL = m8   (8-register group for maximum VL)
     *   tail = ta, mask = ma (all elements active; no mask register)
     *
     * vsetvli stores the resulting VL in t0; we pass n_elems as the
     * *requested* VL.  The hart clips to VLMAX = VLEN × 8 / 64 = VLEN/8.
     */
    unsigned long vl;
    asm volatile(
        "vsetvli %0, %1, e64, m8, ta, ma"
        : "=r"(vl)
        : "r"((unsigned long)n_elems)
    );

    if (cfg->do_store) {
        /*
         * ── THE TLB-stress instruction: vsoxei64.v (scatter store) ─────────
         *
         * Instruction:   vsoxei64.v  v0, (rs1), v8
         *
         * Operands:
         *   v0   – data register group (v0..v7 under LMUL=m8); holds values
         *          to write; each element is 64 bits (SEW=e64)
         *   rs1  – scalar base address = buf
         *   v8   – index register group (v8..v15 under LMUL=m8); each entry
         *          is a 64-bit unsigned byte offset loaded from page_offsets[]
         *
         * Effective address of element i:
         *   EA_i = buf + v8[i]   where v8[i] = page_offsets[i]
         *
         * Because page_offsets[i] is randomly chosen to point into a distinct
         * 4 KiB page for every i, the CPU must perform VL independent virtual-
         * to-physical address translations.  With VLEN=256 and LMUL=m8 there
         * are 32 active elements → up to 32 TLB misses from one instruction.
         *
         * Two-step sequence (both within this asm block):
         *   Step 1:  vle64.v v8, (page_offsets)  – unit-stride contiguous load;
         *            all elements are adjacent → touches a single TLB entry.
         *   Step 2:  vsoxei64.v v0, (buf), v8    – the scatter store; each
         *            element EA_i lands in a different page → maximum TLB pressure.
         */
        asm volatile(
            /* Step 1: load index vector (v8..v15) from page_offsets[] */
            "vle64.v        v8,  (%1)           \n\t"
            /* Fill data vector (v0..v7) with a non-zero canary.
             * vmv.v.i accepts a 5-bit sign-extended immediate [-16..15];
             * we use 5 (0x05) as a convenient non-zero value.
             * The actual data written is irrelevant: only the address
             * translations (TLB misses) matter for this benchmark. */
            "vmv.v.i        v0,  5              \n\t"
            /* ── Step 2: ONE scatter store: EA_i = buf + v8[i] ─────────── */
            "vsoxei64.v     v0,  (%0), v8       \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "v0","v1","v2","v3","v4","v5","v6","v7",
              "v8","v9","v10","v11","v12","v13","v14","v15",
              "memory"
        );
    } else {
        /*
         * ── THE TLB-stress instruction: vloxei64.v (gather load) ───────────
         *
         * Instruction:   vloxei64.v  v0, (rs1), v8
         *
         * Operands:
         *   v0   – destination register group (v0..v7 under LMUL=m8); receives
         *          loaded data; each element is 64 bits (SEW=e64)
         *   rs1  – scalar base address = buf
         *   v8   – index register group (v8..v15 under LMUL=m8); each entry
         *          is a 64-bit unsigned byte offset loaded from page_offsets[]
         *
         * Effective address of element i:
         *   EA_i = buf + v8[i]   where v8[i] = page_offsets[i]
         *
         * Because page_offsets[i] points into a different 4 KiB page for every
         * i, the CPU must issue VL independent TLB lookups.  The loaded values
         * in v0 are discarded; only the address translation side-effects (TLB
         * traffic, page-walk cost) matter for this benchmark.
         *
         * Two-step sequence (both within this asm block):
         *   Step 1:  vle64.v v8, (page_offsets)  – unit-stride contiguous load;
         *            elements are adjacent → touches a single TLB entry.
         *   Step 2:  vloxei64.v v0, (buf), v8    – the gather load; each element
         *            EA_i lands in a different page → maximum TLB pressure.
         */
        asm volatile(
            /* Step 1: load index vector (v8..v15) from page_offsets[] */
            "vle64.v        v8,  (%1)           \n\t"
            /* ── Step 2: ONE gather load: EA_i = buf + v8[i] ───────────── */
            "vloxei64.v     v0,  (%0), v8       \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "v0","v1","v2","v3","v4","v5","v6","v7",
              "v8","v9","v10","v11","v12","v13","v14","v15",
              "memory"
        );
    }
}
