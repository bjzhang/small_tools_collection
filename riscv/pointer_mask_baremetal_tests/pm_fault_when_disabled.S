#ifndef PMM_SHIFT
#define PMM_SHIFT 32
#endif

#ifndef PMM_MASK
#define PMM_MASK 0x3
#endif

#ifndef TAG_MASK
#define TAG_MASK 0xFF00000000000000
#endif

    .section .text
    .globl _start

_start:
    la   t0, trap_handler
    csrw mtvec, t0

    /* Force pointer masking disabled in menvcfg/senvcfg. */
    csrr t0, menvcfg
    li   t1, PMM_MASK
    slli t1, t1, PMM_SHIFT
    not  t1, t1
    and  t2, t0, t1
    csrw menvcfg, t2

    csrr t3, senvcfg
    li   t4, PMM_MASK
    slli t4, t4, PMM_SHIFT
    not  t4, t4
    and  t5, t3, t4
    csrw senvcfg, t5

    la   t0, user_entry
    csrw mepc, t0
    csrr t1, mstatus
    li   t2, ~(3 << 11)
    and  t1, t1, t2       /* MPP = U */
    csrw mstatus, t1
    mret

user_entry:
    la   t0, test_word
    li   t1, TAG_MASK
    or   t0, t0, t1
    ld   t2, 0(t0)        /* Expected to fault when masking disabled */
    li   a0, 0            /* If we got here, test failed */
    ecall

trap_handler:
    csrr t0, mcause
    li   t1, 5            /* Load access fault */
    li   t2, 13           /* Load page fault */
    beq  t0, t1, pass
    beq  t0, t2, pass

    li   t3, 8            /* ECALL from U-mode indicates unexpected non-fault path */
    beq  t0, t3, fail

    la   t4, trap_mcause
    sd   t0, 0(t4)
    csrr t5, mtval
    sd   t5, 8(t4)
    j    fail

pass:
    li   a0, 1
    j    done

fail:
    li   a0, 0

done:
    wfi
    j    done

    .section .bss
    .align 3
test_word:
    .zero 8
trap_mcause:
    .zero 16
