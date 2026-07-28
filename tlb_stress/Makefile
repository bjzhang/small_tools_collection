# Makefile - Build the bare-metal TLB-stress test for AArch64 (SME2) and RISC-V (RVV 1.0)
#
# Targets
#   make arm      → tlb_stress_arm.elf   (cross-compiled for AArch64 + SME2)
#   make riscv    → tlb_stress_riscv.elf (cross-compiled for RV64GCV + RVV 1.0)
#   make all      → both
#   make clean    → remove built files
#
# Required cross-compilers (install via your distro or Linaro/RISC-V toolchains):
#   ARM  : aarch64-linux-gnu-gcc   (or aarch64-none-elf-gcc)
#   RISC-V: riscv64-linux-gnu-gcc  (or riscv64-unknown-elf-gcc)
#
# Override the compiler by passing e.g.:
#   make arm ARM_CC=aarch64-none-elf-gcc

# ── Arm (AArch64 + SME2) ────────────────────────────────────────────────────
ARM_CC      ?= aarch64-linux-gnu-gcc
ARM_MARCH   := armv9-a+sve2
ARM_CFLAGS  := -march=$(ARM_MARCH) -O2 -g \
               -ffreestanding -nostdlib \
               -std=gnu11 -Wall -Wextra \
               -I.
ARM_LDFLAGS := -T arm/linker.ld -nostdlib

ARM_SRCS    := main.c arm/arm_sme.c
ARM_ASM     := arm/startup.S
ARM_OBJS    := $(ARM_SRCS:.c=.arm.o) $(ARM_ASM:.S=.arm.o)
ARM_ELF     := tlb_stress_arm.elf

# ── RISC-V (RV64GCV, RVV 1.0) ───────────────────────────────────────────────
RISCV_CC      ?= riscv64-linux-gnu-gcc
RISCV_MARCH   := rv64gcv
RISCV_MABI    := lp64d
RISCV_CFLAGS  := -march=$(RISCV_MARCH) -mabi=$(RISCV_MABI) -O2 -g \
                 -ffreestanding -nostdlib \
                 -std=gnu11 -Wall -Wextra \
                 -I.
RISCV_LDFLAGS := -T riscv/linker.ld -nostdlib

RISCV_SRCS    := main.c riscv/riscv_rvv.c
RISCV_ASM     := riscv/startup.S
RISCV_OBJS    := $(RISCV_SRCS:.c=.riscv.o) $(RISCV_ASM:.S=.riscv.o)
RISCV_ELF     := tlb_stress_riscv.elf

# ── Default target ───────────────────────────────────────────────────────────
.PHONY: all arm riscv clean

all: arm riscv

arm: $(ARM_ELF)

riscv: $(RISCV_ELF)

# ── Arm compile rules ────────────────────────────────────────────────────────
%.arm.o: %.c
	$(ARM_CC) $(ARM_CFLAGS) -c $< -o $@

%.arm.o: %.S
	$(ARM_CC) $(ARM_CFLAGS) -c $< -o $@

$(ARM_ELF): $(ARM_OBJS)
	$(ARM_CC) $(ARM_LDFLAGS) $(ARM_OBJS) -o $@
	@echo "Built: $@"

# ── RISC-V compile rules ─────────────────────────────────────────────────────
%.riscv.o: %.c
	$(RISCV_CC) $(RISCV_CFLAGS) -c $< -o $@

%.riscv.o: %.S
	$(RISCV_CC) $(RISCV_CFLAGS) -c $< -o $@

$(RISCV_ELF): $(RISCV_OBJS)
	$(RISCV_CC) $(RISCV_LDFLAGS) $(RISCV_OBJS) -o $@
	@echo "Built: $@"

# ── Clean ────────────────────────────────────────────────────────────────────
clean:
	rm -f $(ARM_OBJS) $(ARM_ELF)
	rm -f $(RISCV_OBJS) $(RISCV_ELF)
