/*
 * arm/startup.S - AArch64 bare-metal entry point for QEMU '-M virt'.
 *
 * QEMU virt loads the ELF at 0x40000000 (see linker.ld) and jumps to _start
 * at EL1 with the MMU disabled (flat identity mapping still active for MMIO).
 *
 * This stub:
 *   1. Sets up the stack.
 *   2. Clears the BSS section.
 *   3. Enables FP/SIMD, SVE and SME traps (CPACR_EL1 / SMCR_EL1).
 *   4. Sets SMCR_EL1.LEN to 0xFF to request the maximum Streaming SVE VL.
 *   5. Jumps to main().
 *   6. On return, performs a semihosting SYS_EXIT so QEMU exits cleanly.
 */

.section ".text.boot", "ax"
.global _start

_start:
    /* ── 1. Stack ──────────────────────────────────────────────────────── */
    ldr     x0, =__stack_top
    mov     sp, x0

    /* ── 2. Clear BSS ──────────────────────────────────────────────────── */
    ldr     x1, =__bss_start
    ldr     x2, =__bss_end
.Lbss_clear:
    cmp     x1, x2
    bge     .Lbss_done
    str     xzr, [x1], #8
    b       .Lbss_clear
.Lbss_done:

    /* ── 3. Enable FP/SIMD, SVE (ZEN) and SME (SMEN) at EL0/EL1 ─────── */
    /*
     * CPACR_EL1 fields (no-trap when set to 0b11):
     *   FPEN [21:20] – SIMD/FP
     *   ZEN  [17:16] – SVE
     *   SMEN [25:24] – SME (Streaming SVE mode and ZA array)
     *
     * 3 << 24 = 0x3000000 does not fit in a 12-bit logical immediate so we
     * use a temporary register for the SMEN mask.
     */
    mrs     x0, cpacr_el1
    orr     x0, x0, #(3 << 20)     /* FPEN: no FP trap EL0/EL1  */
    orr     x0, x0, #(3 << 16)     /* ZEN:  no SVE trap EL0/EL1 */
    mov     x1, #(3 << 24)
    orr     x0, x0, x1              /* SMEN: no SME trap EL0/EL1 */
    msr     cpacr_el1, x0
    isb

    /* ── 4. Set SMCR_EL1.LEN to maximum (0xFF → ask for SVL=32×128 b) ── */
    /*
     * SVL = (SMCR_EL1.LEN + 1) × 128 bits; the CPU clips to its supported
     * maximum.  Writing 0xFF requests 32768-bit SVL; QEMU will deliver its
     * highest supported value (typically 2048 bits = 32 × 64-bit elements).
     *
     * SMCR_EL1 = S3_0_C1_C8_0 (op0=3, op1=0, CRn=1, CRm=8, op2=0).
     * Use the generic sys-reg syntax because GCC < 14 doesn't know the
     * 'smcr_el1' mnemonic.
     */
    mov     x0, #0xFF
    msr     S3_0_C1_C8_0, x0        /* SMCR_EL1: request max SVL */
    isb

    /* ── 5. Call main() ────────────────────────────────────────────────── */
    bl      main

    /* ── 6. Semihosting SYS_EXIT (w0 already holds main's return code) ── */
    /*
     * AArch64 semihosting call convention:
     *   w0 = operation number  (0x18 = SYS_EXIT)
     *   x1 = pointer to parameter block {ADP_Stopped_ApplicationExit, retcode}
     *   HLT #0xF000 triggers the semihosting intercept in QEMU.
     */
    mov     w1, w0                  /* save return code               */
    adr     x2, .Lexit_block
    str     x1, [x2, #8]           /* patch exit code into block[1]  */
    mov     w0, #0x18              /* SYS_EXIT                        */
    mov     x1, x2
    hlt     #0xF000

    /* Spin if semihosting is not enabled */
.Lhang:
    wfi
    b       .Lhang

.align 3
.Lexit_block:
    .quad   0x20026       /* ADP_Stopped_ApplicationExit    */
    .quad   0             /* exit code (patched at runtime) */
