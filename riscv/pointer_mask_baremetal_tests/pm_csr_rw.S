#ifndef PMM_SHIFT
#define PMM_SHIFT 32
#endif

#ifndef PMM_MASK
#define PMM_MASK 0x3
#endif

#ifndef PMM_ENABLE_VALUE
#define PMM_ENABLE_VALUE 0x2
#endif

    .section .text
    .globl _start

_start:
    la   t0, trap_handler
    csrw mtvec, t0

    li   a0, 1

    /* Save original menvcfg and try PMM field R/W. */
    csrr t0, menvcfg
    li   t1, PMM_MASK
    slli t1, t1, PMM_SHIFT
    not  t1, t1
    and  t2, t0, t1

    li   t3, PMM_ENABLE_VALUE
    slli t3, t3, PMM_SHIFT
    or   t2, t2, t3
    csrw menvcfg, t2

    csrr t4, menvcfg
    li   t5, PMM_MASK
    slli t5, t5, PMM_SHIFT
    and  t4, t4, t5
    and  t3, t3, t5
    bne  t4, t3, fail

    /* Restore original menvcfg. */
    csrw menvcfg, t0
    j    done

fail:
    li   a0, 0

done:
    j    done

trap_handler:
    la   t6, trap_mcause
    csrr t0, mcause
    sd   t0, 0(t6)
    csrr t1, mtval
    sd   t1, 8(t6)
    li   a0, 0
    j    done

    .section .bss
    .align 3
trap_mcause:
    .zero 16
