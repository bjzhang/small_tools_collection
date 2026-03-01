# Random Vector TLB-Stress Generator

A bare-metal test framework that issues **a single vector load or store
instruction per iteration** engineered to cause the maximum number of TLB
misses.  Two ISA variants are provided:

| Variant | ISA | Key instruction |
|---------|-----|-----------------|
| `arm`   | Armv9-A + SME2, Streaming SVE mode | `ld1d` / `st1d` scatter-gather |
| `riscv` | RISC-V RVV 1.0 | `vloxei64.v` / `vsoxei64.v` indexed |

---

## How the single instruction causes many TLB misses

### Arm (Streaming SVE gather/scatter)

The test enters Streaming SVE mode (`SMSTART SM`) and executes one SVE
*gather load*:

```
ld1d  { z0.d }, p0/z, [x_base, z1.d]
```

Each 64-bit lane `i` reads `test_buf[page_offsets[i]]`.  `page_offsets[i]`
is chosen randomly from a 16 MiB buffer (4096 × 4 KiB pages), so every
lane accesses a **different virtual page**.  With SVL = 2048 bits the
instruction issues 32 independent address translations in one cycle.

Because the 8 MiB eviction sweep (`evict_buf`) executed just before the
test displaces test-buffer translations from the TLB by capacity pressure,
almost all 32 address translations miss the TLB.

### RISC-V (RVV indexed gather/scatter)

One RVV *indexed unordered load* is issued with LMUL = m8 to maximise the
active element count:

```
vloxei64.v  v0, (a_base), v8
```

Lane `i` loads `test_buf[v8[i]]` where `v8[i] = page_offsets[i]`.  Each
element touches a distinct 4 KiB page.  With VLEN = 256 and LMUL = m8,
32 elements are processed; with VLEN = 512, 64 elements.

---

## Directory layout

```
tlb_stress/
├── Makefile
├── README.md
├── common.h          # config struct, PRNG, cycle counter, UART helpers
├── main.c            # main test loop (arch-independent)
├── arm/
│   ├── arm_sme.c     # Arm SME2 / Streaming SVE implementation
│   ├── startup.S     # AArch64 bare-metal entry, SME/SVE enable
│   └── linker.ld     # load at 0x40000000 (QEMU virt DRAM)
└── riscv/
    ├── riscv_rvv.c   # RISC-V RVV 1.0 implementation
    ├── startup.S     # RISC-V bare-metal entry
    └── linker.ld     # load at 0x80200000 (after OpenSBI)
```

---

## Build

### Prerequisites

```bash
# Debian/Ubuntu
sudo apt install gcc-aarch64-linux-gnu gcc-riscv64-linux-gnu

# Or use bare-metal newlib toolchains:
#   aarch64-none-elf-gcc  (Arm toolchain for A-profile)
#   riscv64-unknown-elf-gcc
```

```bash
cd tlb_stress

# Build for Arm (SME2)
make arm

# Build for RISC-V (RVV)
make riscv

# Build both
make
```

Override the compiler if needed:

```bash
make arm   ARM_CC=aarch64-none-elf-gcc
make riscv RISCV_CC=riscv64-unknown-elf-gcc
```

---

## Run under QEMU

### Arm – QEMU command line

```bash
qemu-system-aarch64 \
  -M virt \
  -cpu max,sme=on,sve=on,sme-default-vector-length=64 \
  -m 256M \
  -nographic \
  -semihosting-config enable=on,target=native \
  -kernel tlb_stress_arm.elf
```

Key options:
- `-cpu max` – enables all architectural features including SME2 and SVE.
- `sme-default-vector-length=64` – sets SVL to 64 bytes (512 bits); use
  `256` for maximum (2048 bits = 32 × 64-bit elements per instruction).
- `-semihosting-config enable=on` – allows the firmware to call `exit()` via
  `HLT #0xF000`; omit if not needed.

### RISC-V – QEMU command line

```bash
qemu-system-riscv64 \
  -M virt \
  -cpu rv64,v=true,vext_spec=v1.0,vlen=256,elen=64 \
  -m 256M \
  -nographic \
  -bios default \
  -kernel tlb_stress_riscv.elf
```

Key options:
- `v=true,vext_spec=v1.0` – enables the RVV 1.0 extension.
- `vlen=256` – sets the hart's VLEN.  Use `vlen=512` for 64 elements per op.
- `-bios default` – loads OpenSBI as M-mode firmware; the ELF is placed at
  0x80200000 (S-mode entry).

---

## Observing TLB-miss behaviour in QEMU

QEMU does not expose real TLB-miss hardware performance counters, but the
following methods approximate TLB-miss cost:

### 1. Cycle-count output (built-in)

The test already prints, for every iteration:
```
iter=0 pages=32 cycles=<delta>
```
Iterations where the eviction sweep is effective show **higher** cycle counts
for the single vector instruction (due to QEMU's software TLB refill
overhead).  Compare against a baseline run with `EVICT_PAGES` set to 0.

### 2. QEMU tracing (`-d`)

```bash
# Arm
qemu-system-aarch64 ... -d mmu -D /tmp/qemu_mmu.log

# RISC-V
qemu-system-riscv64 ... -d mmu -D /tmp/qemu_mmu.log
```

`-d mmu` logs every software TLB (SOFTMMU) miss, fill, and flush.  Each
`ldq_mmu` / `stq_mmu` log entry in the file corresponds to one element
address translation that missed QEMU's internal TLB (256 entries per
address-space index by default).

Count entries per instruction epoch:
```bash
grep -c 'ldq_mmu' /tmp/qemu_mmu.log
```

### 3. Perf / PMU counters (Linux guest)

If the test is adapted to run in Linux userspace, `perf stat` with the
`dTLB-load-misses` and `dTLB-store-misses` events gives precise counts on
real hardware.  On QEMU, these events are not virtualised but the cycle
delta from (1) serves as a proxy.

### 4. QEMU plugin (`-plugin`)

QEMU's `insn` plugin API can count memory accesses per instruction.
Build with `--enable-plugins` and use the `libinsn.so` example to count
memory ops for each `ld1d`/`vloxei64.v` invocation.

---

## Tuning parameters (`common.h`)

| Macro | Default | Description |
|-------|---------|-------------|
| `BUF_PAGES` | 4096 | Pages in the test buffer (16 MiB) |
| `EVICT_PAGES` | 2048 | Pages swept before each test (8 MiB) |
| `MAX_PAGES_TESTED` | 32 | Max elements (pages) per single vector op |
| `DEFAULT_ITERS` | 200 | Number of test iterations |
| `DEFAULT_SEED` | `0xDEADBEEFCAFEULL` | PRNG seed |

Set `do_store = 1` in `main.c` to switch from gather load to scatter store.
