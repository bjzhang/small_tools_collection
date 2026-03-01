/*
 * common.h - Shared types, configuration, PRNG and helpers for the
 *            bare-metal random vector TLB-stress test.
 *
 * Each test iteration issues EXACTLY ONE vector gather-load or scatter-store
 * instruction whose element addresses span many distinct 4 KiB pages,
 * maximising TLB-miss pressure on a single instruction.
 */
#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>

/* ── Memory layout ──────────────────────────────────────────────────────── */
#define PAGE_SIZE           4096U
#define BUF_PAGES           4096U       /* test buffer: 4096 × 4 KiB = 16 MiB  */
#define BUF_SIZE            ((uint64_t)BUF_PAGES * PAGE_SIZE)
#define EVICT_PAGES         2048U       /* eviction sweep: 2048 × 4 KiB = 8 MiB */

/*
 * Maximum vector elements (pages) touched by one vector instruction.
 * 32 covers SVE up to SVL=2048 b (32 × 64-bit lanes) and
 * RVV up to VLEN=256 with LMUL=m8 (32 × 64-bit elements).
 */
#define MAX_PAGES_TESTED    32U

/* ── Test configuration ──────────────────────────────────────────────────── */
typedef struct {
    uint64_t seed;              /* PRNG seed                             */
    unsigned iterations;        /* number of test iterations             */
    unsigned page_size;         /* assumed page size (bytes)             */
    unsigned max_pages_per_test;/* pages touched per single vector op    */
    int      do_store;          /* 1 = scatter store, 0 = gather load    */
    int      indexed;           /* 1 = gather/scatter, 0 = contiguous    */
} tlb_config_t;

#define DEFAULT_SEED    0xDEADBEEFCAFEULL
#define DEFAULT_ITERS   200U

/* ── xorshift64 PRNG ─────────────────────────────────────────────────────── */
static inline uint64_t xorshift64(uint64_t *s)
{
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    return *s;
}

/* ── Cycle counter ───────────────────────────────────────────────────────── */
static inline uint64_t read_cycle_counter(void)
{
    uint64_t v;
#if defined(__aarch64__)
    /* Virtual count register – always accessible from EL0/EL1 */
    asm volatile("mrs %0, cntvct_el0" : "=r"(v));
#elif defined(__riscv)
    asm volatile("rdcycle %0" : "=r"(v));
#else
    v = 0;
#endif
    return v;
}

/* ── Minimal bare-metal UART output ──────────────────────────────────────── */
/*
 * QEMU virt machines expose a UART at well-known MMIO addresses.
 * Writing a byte to the data register is sufficient; no initialisation
 * is needed because QEMU keeps the UART ready from reset.
 */
#if defined(__aarch64__)
# define UART_BASE  ((volatile uint32_t *)0x09000000UL)  /* PL011 DR */
static inline void uart_putc(char c)
{
    *UART_BASE = (uint32_t)(unsigned char)c;
}
#elif defined(__riscv)
# define UART_BASE  ((volatile uint8_t *)0x10000000UL)  /* 16550 THR */
static inline void uart_putc(char c)
{
    *UART_BASE = (uint8_t)c;
}
#else
static inline void uart_putc(char c) { (void)c; }
#endif

static inline void uart_puts(const char *s)
{
    while (*s)
        uart_putc(*s++);
}

/* Print unsigned 64-bit decimal */
static inline void uart_putu64(uint64_t v)
{
    char buf[21];
    int  i = sizeof(buf) - 1;
    buf[i] = '\0';
    if (v == 0) { uart_putc('0'); return; }
    while (v && i > 0) { buf[--i] = '0' + (int)(v % 10); v /= 10; }
    uart_puts(&buf[i]);
}

/* ── Architecture-specific test function (implemented per arch) ──────────── */
/*
 * Issue EXACTLY ONE vector load (do_store==0) or store (do_store==1).
 * page_offsets[0..n_elems-1] are byte offsets from buf; each offset
 * points into a distinct 4 KiB page to maximise TLB-miss pressure.
 */
void run_vector_test(const tlb_config_t    *cfg,
                     volatile uint8_t      *buf,
                     const uint64_t        *page_offsets,
                     unsigned               n_elems);

#endif /* COMMON_H */
