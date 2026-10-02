# Engine

## WISA — 8-bit ISA

WISA means **Waveform Instruction Set Architecture**. It is a small programmable I/O instruction set: a program describes pin values, timing, and input-dependent actions instead of selecting a fixed UART, SPI, or I²C peripheral.

This draft uses 8-bit opcode bytes and optional operand bytes. It is a design target, not an implemented feature of the current RTL. The host programming interface remains open. The alternative fixed-word ISA is described in TBD.

### State

| State | Meaning |
| --- | --- |
| `PC` | 8-bit byte address of the next opcode; program capacity is 256 bytes. |
| `A` | 8-bit data register for input samples, output values, and shifted data. |
| `X` | 8-bit loop counter. |
| `PINS` | Eight bidirectional `uio` pins; reads use `uio_in`, writes update the `uio_out` latch. |
| `DIR` | Eight output-enable bits; 1 drives a pin, 0 leaves it as an input. |

A retains a byte independently of the pin output latch. MOV A,PINS stores an input sample; SHL/SHR operate on that stored byte; MOV PINS,A writes it to the output latch; JNZ tests it. A is useful for data-dependent transfers and input processing, but the constant UART example below does not use it. Arithmetic addition is not required for these functions.

Reset sets PC, A, X, output latch, and DIR to zero. All pins are inputs. Execution begins at byte address 0 when reset is released with a program available. Physical asynchronous inputs require synchronization; WAIT and input reads use the resulting digital input values.

### Operand notation

| Operand | Meaning |
| --- | --- |
| `imm8` | An unsigned 8-bit immediate: a literal value encoded directly in the program, from 0 to 255 (`0x00`–`0xFF`). It is not a register or an address to dereference. |
| `addr8` | An unsigned 8-bit opcode byte address used as a branch target. |
| `pin` | Input pin index, 0–7. |
| `level` | Required input level, 0 or 1. |

In this byte-oriented ISA, imm8 and addr8 occupy the byte immediately after the opcode. For example, SET PINS,0x01 encodes as bytes `12 01`; DELAY 255 encodes as `40 FF`. A symbolic imm8 in the instruction table is a placeholder replaced by the actual value. WAIT encodes pin and level in its opcode and has no operand byte.

### Instructions

Most instructions contain one opcode byte. Instructions with an immediate or address contain one following operand byte. Branch targets are byte addresses and must point to opcodes, not operands.

| Opcode | Instruction | Bytes | Operation |
| --- | --- | ---: | --- |
| `0x00` | `NOP` | 1 | Do nothing. |
| `0x01` | `HALT` | 1 | Stop execution; retain output latch and DIR. |
| `0x10` | `MOV A, PINS` | 1 | Sample all eight input pins into A. |
| `0x11` | `MOV PINS, A` | 1 | Write A to the output latch. |
| `0x12` | `SET PINS, imm8` | 2 | Write the following byte to the output latch. |
| `0x13` | `SET DIR, imm8` | 2 | Set output enables from the following byte. |
| `0x14` | `PULL A` |	1	| Read one byte from the engine's input FIFO into A and remove it from the FIFO. If empty, stall until a byte is available. |
| `0x15` | `PUSH A`	| 1	| Write A to the engine's output FIFO. If full, stall until space is available. |
| `0x20` | `SET A, imm8` | 2 | Load A. |
| `0x22` | `XOR A, imm8` | 2 | XOR A with the immediate. |
| `0x23` | `SHL A` | 1 | Shift left; fill bit0 with zero and discard bit7. |
| `0x24` | `SHR A` | 1 | Shift right; fill bit7 with zero and discard bit0. |
| `0x25` | `SET X, imm8` | 2 | Load X. |
| `0x30–0x3F` | `WAIT pin, level` | 1 | Hold PC until the selected input equals the selected level. |
| `0x40` | `DELAY imm8` | 2 | Stall for 0–255 extra clocks after reading the operand. |
| `0x50` | `JMP addr8` | 2 | Jump to an opcode byte address. |
| `0x51` | `JNZ A, addr8` | 2 | Jump if A is nonzero. |
| `0x52` | `LOOP X, addr8` | 2 | Decrement X modulo 256; jump if the result is nonzero. |

Compared with the original PIO table, HALT is added and ADD A is omitted from the base ISA. Opcode `0x21` is reserved. Other unspecified opcodes are also reserved and must not execute as valid instructions.

For WAIT, `opcode = 0x30 | (level << 3) | pin`, where level is 0 or 1 and pin is 0–7. For example, `WAIT 5, 1` encodes as `0x3D`. WAIT tests a level; waiting for a transition requires waiting for the opposite level first.

SET PINS and MOV PINS update all eight output-latch bits; DIR determines which bits physically drive pins. LOOP with initial X=0 wraps to 255 on its first decrement and runs 256 iterations in the usual counter loop.

### Timing

A single-byte instruction takes one clock. A two-byte instruction takes two: read the opcode first, then read the operand and apply the operation. Unless branching, PC advances by the instruction length. WAIT keeps PC fixed until its condition matches.

DELAY occupies `2 + imm8` clocks. DELAY 0 still occupies its two instruction clocks. A following instruction begins after those clocks. All output changes occur on core-clock rising edges.

This timing profile assumes one instruction byte is available each clock, without hidden fetch stalls. An RTL implementation with additional memory/fetch cycles must define a different timing profile and adjust program delays accordingly.

HALT is distinct from reset: it preserves driven levels. Program execution must not fall through past the loaded image. Branches must stay within it; a program must not depend on PC wraparound.

### What these instructions can do

- Generate finite digital waveforms, pulses, and repetitive patterns.
- Generate UART TX frames using output writes and timed holds.
- Generate SPI clock/data/chip-select patterns; read inputs at programmed points.
- Synchronize execution to an input level or transition using WAIT.
- Repeat short sequences using X and LOOP, or react to sampled data using A and JNZ.
- Release a pin by clearing its DIR bit. Driving an open-drain-style line low requires its output latch to be zero; releasing it requires DIR=0 and an external pull-up.

Protocol framing, bit order, sampling points, and error handling are program responsibilities. These primitives do not automatically provide a complete UART receiver, SPI peripheral, or I²C controller. They do not guarantee transitions on every clock while two-byte instructions execute.

### Example: UART TX, 0x55, 8N1

Use a 50 MHz core and GPIO0 as TX. The requested baud is 115200; a bit interval of 434 clocks gives approximately 115207.37 baud. Other pins remain inputs. The example sends one constant byte, least-significant bit first, followed by one stop bit.

```asm
SET PINS, 0x01    ; Idle HIGH before enabling GPIO0.
SET DIR, 0x01     ; GPIO0 output; other pins inputs.
SET PINS, 0       ; Start.
DELAY 255
DELAY 173
SET PINS, 1       ; Data0 = 1.
DELAY 255
DELAY 173
SET PINS, 0       ; Data1 = 0.
DELAY 255
DELAY 173
SET PINS, 1       ; Data2 = 1.
DELAY 255
DELAY 173
SET PINS, 0       ; Data3 = 0.
DELAY 255
DELAY 173
SET PINS, 1       ; Data4 = 1.
DELAY 255
DELAY 173
SET PINS, 0       ; Data5 = 0.
DELAY 255
DELAY 173
SET PINS, 1       ; Data6 = 1.
DELAY 255
DELAY 173
SET PINS, 0       ; Data7 = 0.
DELAY 255
DELAY 173
SET PINS, 1       ; Stop.
DELAY 255
DELAY 174
HALT
```

For each nonfinal bit, the interval from its output write to the next output write is:

```text
DELAY 255: 2 + 255 clocks
DELAY 173: 2 + 173 clocks
next SET PINS: 2 clocks
total: 434 clocks
```

For the final stop bit, DELAY 174 replaces DELAY 173 because the following HALT takes one clock instead of the two-clock SET. HALT occurs exactly 434 clocks after the stop-bit write. The program occupies **65 bytes**; HALT is at byte address `0x40`.

Offsets below are measured from the start-bit output write. Each interval holds a level; interval ends are exclusive. One bit lasts 8.68 µs and the frame lasts 86.8 µs.

| Segment | Start, clocks | End, clocks | GPIO0 |
| --- | ---: | ---: | --- |
| Start | 0 | 434 | LOW |
| Data0 = 1 | 434 | 868 | HIGH |
| Data1 = 0 | 868 | 1302 | LOW |
| Data2 = 1 | 1302 | 1736 | HIGH |
| Data3 = 0 | 1736 | 2170 | LOW |
| Data4 = 1 | 2170 | 2604 | HIGH |
| Data5 = 0 | 2604 | 3038 | LOW |
| Data6 = 1 | 3038 | 3472 | HIGH |
| Data7 = 0 | 3472 | 3906 | LOW |
| Stop | 3906 | 4340 | HIGH |

After clock 4340, HALT retains GPIO0 HIGH. Before the start bit, TX is also HIGH.

## Current RTL status


## How to test the current RTL

Run `make` from the `test` directory. The supplied description says the existing Cocotb test checks that inputs 20 and 30 produce an output of 50. That test does not validate this ISA or the UART program.

## External hardware
