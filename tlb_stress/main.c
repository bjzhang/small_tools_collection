/*
 * main.c - Main test loop for the bare-metal random vector TLB-stress test.
 *
 * Algorithm per iteration
 * ─────────────────────────────────────────────────────────────────────────
 * 1. Use xorshift64 PRNG to pick n_elems distinct random pages from test_buf.
 * 2. Touch every page in evict_buf sequentially to flush TLB entries that
 *    correspond to the upcoming test pages (capacity-based eviction).
 * 3. Snapshot the cycle counter.
 * 4. Call run_vector_test() → issues EXACTLY ONE gather-load or scatter-store.
 * 5. Snapshot the cycle counter again and log the delta.
 *
 * Compile-time selection of the arch-specific backend is done by linking
 * either arm/arm_sme.c or riscv/riscv_rvv.c (see Makefile).
 */

#include "common.h"

/* ── Static buffers (in BSS) ─────────────────────────────────────────────── */

/*
 * test_buf: the region whose pages will be targeted by the single vector op.
 * PAGE_SIZE alignment ensures that page_index × PAGE_SIZE falls on a true page
 * boundary, giving each element a distinct virtual page.
 */
static volatile uint8_t __attribute__((aligned(PAGE_SIZE)))
    test_buf[BUF_SIZE];

/*
 * evict_buf: swept sequentially before each test to evict the TLB entries
 * for test_buf pages via capacity pressure (no privileged TLBI needed).
 */
static volatile uint8_t __attribute__((aligned(PAGE_SIZE)))
    evict_buf[EVICT_PAGES * PAGE_SIZE];

/* Scatter/gather offset array passed to run_vector_test() */
static uint64_t page_offsets[MAX_PAGES_TESTED];

/* ── Entry point ─────────────────────────────────────────────────────────── */
int main(void)
{
    tlb_config_t cfg = {
        .seed               = DEFAULT_SEED,
        .iterations         = DEFAULT_ITERS,
        .page_size          = PAGE_SIZE,
        .max_pages_per_test = MAX_PAGES_TESTED,
        .do_store           = 0,  /* gather load by default */
        .indexed            = 1,  /* scatter/gather addressing */
    };

    uint64_t prng   = cfg.seed;
    unsigned n      = cfg.max_pages_per_test;

    uart_puts("TLB stress test start\n");
    uart_puts("mode=");
    uart_puts(cfg.do_store ? "scatter-store" : "gather-load");
    uart_puts(" pages_per_op=");
    uart_putu64(n);
    uart_puts(" iterations=");
    uart_putu64(cfg.iterations);
    uart_puts("\n");

    for (unsigned iter = 0; iter < cfg.iterations; iter++) {

        /* ── Step 1: Select n random, distinct-page offsets ─────────────── */
        /*
         * page_offsets[i] = page_idx × PAGE_SIZE = page_idx × 4096
         *
         * BUF_PAGES = 4096 = 2^12, so the modulo is unbiased for any 64-bit
         * xorshift64 output.
         *
         * Virtual address bit breakdown (when MMU enabled under an OS):
         *   EA_i[11: 0] = 0x000                   (page-aligned; offset=0)
         *   EA_i[20:12] = page_idx[8:0]            → indexes a leaf PTE
         *   EA_i[29:21] = page_idx[11:9] + base    → indexes an L2/PMD entry
         *
         * With BUF_PAGES=4096 pages across 8 L2 entries (512 pages each),
         * 32 random draws exercise ≈7.9 out of 8 L2 entries per iteration.
         * Each distinct page_idx produces a distinct virtual page number (VPN)
         * → requires a distinct TLB entry and, on a miss, a separate full
         * page-table walk.  See "Page Table Pattern" in README.md.
         */
        for (unsigned i = 0; i < n; i++) {
            uint64_t page_idx  = xorshift64(&prng) % BUF_PAGES;
            page_offsets[i]    = page_idx * PAGE_SIZE;
        }

        /* ── Step 2: TLB eviction sweep ──────────────────────────────────── */
        /*
         * Reading one byte per page from the eviction buffer forces the
         * hardware TLB to cache evict_buf translations; those occupy the
         * same TLB sets as test_buf translations, evicting them by capacity.
         */
        for (unsigned p = 0; p < EVICT_PAGES; p++) {
            volatile uint8_t dummy = evict_buf[p * PAGE_SIZE];
            (void)dummy;
        }

        /* ── Step 3: Time the single vector instruction ───────────────────── */
        uint64_t t0 = read_cycle_counter();

        run_vector_test(&cfg, test_buf, page_offsets, n);

        uint64_t t1 = read_cycle_counter();

        /* ── Step 4: Report ──────────────────────────────────────────────── */
        uart_puts("iter=");
        uart_putu64(iter);
        uart_puts(" pages=");
        uart_putu64(n);
        uart_puts(" cycles=");
        uart_putu64(t1 - t0);
        uart_puts("\n");
    }

    uart_puts("TLB stress test complete\n");
    return 0;
}
