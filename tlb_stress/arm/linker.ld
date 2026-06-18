/*
 * arm/linker.ld - AArch64 linker script for QEMU '-M virt'.
 *
 * QEMU virt places DRAM at 0x40000000 and jumps to the load address when
 * using '-kernel <elf>'.  The stack sits at the top of a 128 KiB region
 * appended after BSS.
 */
OUTPUT_FORMAT("elf64-littleaarch64")
OUTPUT_ARCH(aarch64)
ENTRY(_start)

SECTIONS
{
    . = 0x40000000;

    /* Code: boot stub first so _start is at the entry address */
    .text : {
        *(.text.boot)
        *(.text*)
    }

    .rodata : { *(.rodata*) }

    . = ALIGN(8);
    .data : { *(.data*) }

    . = ALIGN(8);
    __bss_start = .;
    .bss : {
        *(.bss*)
        *(COMMON)
    }
    . = ALIGN(8);
    __bss_end = .;

    /* 128 KiB stack */
    . = ALIGN(4096);
    . += 0x20000;
    __stack_top = .;
}
