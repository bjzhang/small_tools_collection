/*
 * riscv/riscv_rvv.c - RISC-V RVV 1.0 vector TLB-stress test.
 *
 * TLB-miss strategy
 * ─────────────────
 * A single RVV *indexed unordered load* (vloxei64.v) or
 * *indexed unordered store* (vsoxei64.v) is issued with the maximum
 * vector length supported by the hart.  Each element's effective address is:
 *
 *   addr_i = buf + index_vec[i]            (64-bit byte offset)
 *
 * where index_vec[i] = page_offsets[i] points into a distinct 4 KiB page
 * chosen at random by main.c.  With VLEN=256 and LMUL=m8, 32 elements
 * are processed by one instruction, causing up to 32 TLB misses.
 *
 * LMUL=m8 (8-register group) is used to maximise active elements:
 *   elements = floor(VLEN × LMUL / EEW) = floor(VLEN × 8 / 64) = VLEN/8
 *
 * Register allocation under LMUL=m8:
 *   v0..v7   – destination data  (gather load result / scatter store source)
 *   v8..v15  – index vector      (64-bit byte offsets into buf)
 *   v16..v23 – temporary for loading the index from page_offsets[]
 *
 * Note: RVV requires EEW of the *index* operand to be 64-bit (ei64) so that
 * offsets can address the full 64-bit virtual address space.
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
         * ── THE TLB-stress instruction: indexed unordered scatter store ────
         *
         *   vsoxei64.v v0, (a_base), v8
         *
         * v0  register group (v0..v7)  – store data (canary 0x5A)
         * a_base – base address of buf
         * v8  register group (v8..v15) – 64-bit byte offsets from page_offsets[]
         *
         * Element i writes buf[page_offsets[i]], each in a distinct 4 KiB page
         * → up to VL independent TLB misses from a single instruction.
         */
        asm volatile(
            /* Load index vector (v8..v15) from page_offsets[] */
            "vle64.v        v8,  (%1)           \n\t"
            /* Fill data vector (v0..v7) with a non-zero canary.
             * vmv.v.i accepts a 5-bit sign-extended immediate [-16..15];
             * we use 5 (0x05) as a convenient non-zero value.
             * The actual data written is irrelevant: only the address
             * translations (TLB misses) matter for this benchmark. */
            "vmv.v.i        v0,  5              \n\t"
            /* ── ONE indexed scatter store (the TLB-stress instruction) ── */
            "vsoxei64.v     v0,  (%0), v8       \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "v0","v1","v2","v3","v4","v5","v6","v7",
              "v8","v9","v10","v11","v12","v13","v14","v15",
              "memory"
        );
    } else {
        /*
         * ── THE TLB-stress instruction: indexed unordered gather load ──────
         *
         *   vloxei64.v v0, (a_base), v8
         *
         * v0  register group (v0..v7)  – load destination (result discarded)
         * a_base – base address of buf
         * v8  register group (v8..v15) – 64-bit byte offsets from page_offsets[]
         *
         * Element i reads buf[page_offsets[i]], each in a distinct 4 KiB page
         * → up to VL independent TLB misses from a single instruction.
         */
        asm volatile(
            /* Load index vector (v8..v15) from page_offsets[] */
            "vle64.v        v8,  (%1)           \n\t"
            /* ── ONE indexed gather load (the TLB-stress instruction) ── */
            "vloxei64.v     v0,  (%0), v8       \n\t"
            :
            : "r"(buf), "r"(page_offsets)
            : "v0","v1","v2","v3","v4","v5","v6","v7",
              "v8","v9","v10","v11","v12","v13","v14","v15",
              "memory"
        );
    }
}
