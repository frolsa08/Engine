## PIO instruction set (draft)

The goal is a small programmable I/O engine: firmware describes pin transitions and timing, rather than selecting a fixed UART, SPI, or I2C peripheral. This is the proposed first ISA version; it is a design target and is not implemented in the current RTL yet. The host programming interface is still open.

### State

- `PC`: 8-bit byte address of the next opcode.
- `A`: 8-bit accumulator used for sampled and transmitted data.
- `X`: 8-bit loop counter.
- `PINS`: the 8 bidirectional `uio` pins. `IN` samples `uio_in`; `OUT` updates `uio_out`.
- `DIR`: output-enable bits for `PINS`; 1 drives the corresponding pin and 0 leaves it as an input.

On reset, execution starts at byte address 0 and all pins are inputs.

### Instructions

Instructions are byte-oriented. Most operations are a single opcode byte; operations that need an 8-bit value or address take one extension byte immediately after the opcode. The program occupies up to 256 bytes. Branch addresses are byte addresses and must point to an opcode, not an extension byte. The high nibble selects the operation group, keeping decode simple while avoiding a wasted operand byte on basic pin operations.

| Opcode | Instruction | Length | Operand and operation |
| --- | --- | --- | --- |
| `8'b0000_0000` | `NOP` | 1 byte | Do nothing. |
| `8'b0001_0000` | `MOV A, PINS` | 1 byte | Sample all 8 pins into `A`. |
| `8'b0001_0001` | `MOV PINS, A` | 1 byte | Write `A` to the output latch for all 8 pins. |
| `8'b0001_0010` | `SET PINS, imm8` | 2 bytes | Next byte is the output-latch value. |
| `8'b0001_0011` | `SET DIR, imm8` | 2 bytes | Next byte is the direction mask; 1 is output, 0 is input. |
| `8'b0010_0000` | `SET A, imm8` | 2 bytes | Load the next byte into `A`. |
| `8'b0010_0001` | `ADD A, imm8` | 2 bytes | Add the next byte to `A` modulo 256. |
| `8'b0010_0010` | `XOR A, imm8` | 2 bytes | XOR the next byte with `A`. |
| `8'b0010_0011` | `SHL A` | 1 byte | Shift `A` left one bit; discard the shifted-out bit. |
| `8'b0010_0100` | `SHR A` | 1 byte | Shift `A` right one bit; discard the shifted-out bit. |
| `8'b0010_0101` | `SET X, imm8` | 2 bytes | Load the next byte into loop counter `X`. |
| `8'b0011_LPPP` | `WAIT pin, level` | 1 byte | Opcode bits `[3]` are `level`; bits `[2:0]` select pin 0-7. `LPPP` is a bit-field notation, not a literal to paste into Verilog. |
| `8'b0100_0000` | `DELAY imm8` | 2 bytes | Next byte is the number of extra clock cycles to stall; zero adds no stall cycles. |
| `8'b0101_0000` | `JMP addr` | 2 bytes | Next byte is the target opcode byte address. |
| `8'b0101_0001` | `JNZ A, addr` | 2 bytes | If `A != 0`, branch to the target address in the next byte; otherwise continue. |
| `8'b0101_0010` | `LOOP X, addr` | 2 bytes | Decrement `X`; if the result is not zero, branch to the target address in the next byte. |

For `WAIT`, the opcode is `8'b0011_0000 | {4'b0000, level, pin[2:0]}`. For example, `WAIT pin 5, 1` is `8'b0011_1101`. Single-byte instructions take one clock cycle. Two-byte instructions take two cycles: the opcode is read first, then the extension byte is read and the operation takes effect. Unless a branch is taken, `PC` advances by the instruction length (1 or 2 bytes) to the next opcode. `WAIT` holds its `PC` until the selected pin matches; `DELAY` adds its specified stall cycles after reading the extension byte. Thus the timing cost of every instruction is explicit. Repeated `WAIT` and `JMP` instructions can synchronize to edges; `LOOP` and `DELAY` provide compact timing loops.

## Current RTL status

The current RTL is still the Tiny Tapeout template example: it adds the 8-bit values on `ui_in` and `uio_in`, and places the result on `uo_out`. The PIO engine described above has not been implemented yet.

## How to test

Run `make` from the `test` directory. The current Cocotb test checks that inputs 20 and 30 produce an output of 50.

## External hardware

No external hardware is required for the current example.
