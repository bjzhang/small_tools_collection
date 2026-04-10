# RISC-V Pointer Mask Bare-Metal Testcases

These testcases are standalone RV64 bare-metal assembly tests for pointer masking behavior described in the RISC-V unified DB (Pointer Masking extensions such as Smnpm/Ssnpm/Smmpm where applicable).

## Files

- `pm_csr_rw.S` — checks PMM CSR field write/read behavior.
- `pm_jalr_mask_u_mode.S` — checks control-flow pointer masking with `jalr` in U-mode.
- `pm_load_store_mask_u_mode.S` — checks data pointer masking on load/store in U-mode.
- `pm_fault_when_disabled.S` — checks tagged-pointer access traps when masking is disabled.

## Conventions

Each test:

- Uses `_start` as entry.
- Writes `a0 = 1` on pass and `a0 = 0` on fail.
- Ends in an infinite loop at `done`.
- Uses a trap handler that records `mcause` and `mtval` in memory.

## Configuration knobs

Pointer masking field placement/value is implementation/spec-version dependent. These tests expose compile-time knobs with safe defaults:

- `PMM_SHIFT` (default: `32`)
- `PMM_MASK` (default: `0x3`)
- `PMM_ENABLE_VALUE` (default: `0x2`)
- `TAG_MASK` (default: `0xFF00000000000000`)

Override them with your assembler command line, for example:

```bash
riscv64-unknown-elf-gcc -nostdlib -march=rv64gc_zicsr -mabi=lp64 \
  -DPMM_SHIFT=32 -DPMM_MASK=0x3 -DPMM_ENABLE_VALUE=0x2 \
  -DTAG_MASK=0xFF00000000000000 \
  -T your_linker_script.ld pm_jalr_mask_u_mode.S -o pm_jalr_mask_u_mode.elf
```

## Notes

- These tests assume M-mode entry and that dropping to U-mode is allowed.
- If your platform lacks S-mode/U-mode or pointer masking support, trap behavior may differ.
- For platform bring-up, inspect `trap_mcause`/`trap_mtval` symbols in memory to debug failures.
