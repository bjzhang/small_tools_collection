/*
 * riscv/linker.ld - RISC-V 64-bit linker script for QEMU '-M virt'.
 *
 * QEMU virt places DRAM at 0x80000000.  OpenSBI (QEMU's default firmware)
 * loads the next-stage binary at 0x80200000, so we place the bare-metal
 * kernel at that address to be compatible with the default QEMU setup.
 * If '-bios none' is used, set load address to 0x80000000.
 */
OUTPUT_FORMAT("elf64-littleriscv")
OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
    . = 0x80200000;

    /* Code: boot stub first */
    .text : {
        *(.text.boot)
        *(.text*)
    }

    .rodata : { *(.rodata*) }

    . = ALIGN(8);
    .data : { *(.data*) }

    /* Small-data section for gp-relative addressing */
    . = ALIGN(8);
    __global_pointer$ = . + 0x800;
    .sdata : { *(.sdata*) }

    . = ALIGN(8);
    __bss_start = .;
    .sbss  : { *(.sbss*)  }
    .bss   : { *(.bss*)   *(COMMON) }
    . = ALIGN(8);
    __bss_end = .;

    /* 128 KiB stack */
    . = ALIGN(4096);
    . += 0x20000;
    __stack_top = .;
}
