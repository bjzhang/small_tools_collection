#ifndef PMM_SHIFT
#define PMM_SHIFT 32
#endif

#ifndef PMM_MASK
#define PMM_MASK 0x3
#endif

#ifndef PMM_ENABLE_VALUE
#define PMM_ENABLE_VALUE 0x2
#endif

#ifndef TAG_MASK
#define TAG_MASK 0xFF00000000000000
#endif

    .section .text
    .globl _start

_start:
    la   t0, trap_handler
    csrw mtvec, t0

    /* Enable pointer masking in menvcfg/senvcfg. */
    csrr t0, menvcfg
    li   t1, PMM_MASK
    slli t1, t1, PMM_SHIFT
    not  t1, t1
    and  t2, t0, t1
    li   t3, PMM_ENABLE_VALUE
    slli t3, t3, PMM_SHIFT
    or   t2, t2, t3
    csrw menvcfg, t2

    csrr t4, senvcfg
    li   t5, PMM_MASK
    slli t5, t5, PMM_SHIFT
    not  t5, t5
    and  t6, t4, t5
    or   t6, t6, t3
    csrw senvcfg, t6

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

    li   t2, 0x1122334455667788
    sd   t2, 0(t0)
    ld   t3, 0(t0)
    bne  t2, t3, user_fail

    li   a0, 1
    ecall

user_fail:
    li   a0, 0
    ecall

trap_handler:
    csrr t0, mcause
    li   t1, 8            /* ECALL from U-mode */
    beq  t0, t1, done

    la   t2, trap_mcause
    sd   t0, 0(t2)
    csrr t3, mtval
    sd   t3, 8(t2)
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
