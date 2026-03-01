/*
 * riscv/startup.S - RISC-V 64-bit bare-metal entry point for QEMU '-M virt'.
 *
 * QEMU virt places DRAM at 0x80000000 and jumps to _start.
 *
 * This stub:
 *   1. Sets the global pointer (gp) for relaxation.
 *   2. Sets up the stack pointer.
 *   3. Clears the BSS section.
 *   4. Calls main().
 *   5. Loops forever if main() returns (or use SBI shutdown if available).
 *
 * Vector extension (RVV) needs no explicit enable on RISC-V; the hart exposes
 * it once '-cpu rv64,v=true' is passed to QEMU.
 */

.option norelax
.section ".text.boot", "ax"
.global _start

_start:
    /* ── 1. Set global pointer ────────────────────────────────────────── */
.option push
.option norelax
    la      gp, __global_pointer$
.option pop

    /* ── 2. Stack ─────────────────────────────────────────────────────── */
    la      sp, __stack_top

    /* ── 3. Clear BSS ─────────────────────────────────────────────────── */
    la      t0, __bss_start
    la      t1, __bss_end
.Lbss_clear:
    bgeu    t0, t1, .Lbss_done
    sd      zero, (t0)
    addi    t0, t0, 8
    j       .Lbss_clear
.Lbss_done:

    /* ── 4. Call main() ───────────────────────────────────────────────── */
    call    main

    /* ── 5. SBI system reset (ecall to M-mode firmware) ──────────────── */
    /*
     * SBI System Reset Extension (EID=0x53525354, FID=0):
     *   a7 = 0x53525354  (EID: SRST)
     *   a6 = 0           (FID: sbi_system_reset)
     *   a0 = 0           (reset_type: shutdown)
     *   a1 = 0           (reset_reason: no reason)
     */
    li      a7, 0x53525354
    li      a6, 0
    mv      a0, zero                /* reset_type  = 0 (shutdown) */
    mv      a1, zero                /* reset_reason = 0 (no reason) */
    ecall

    /* Spin if SBI is not available */
.Lhang:
    wfi
    j       .Lhang
