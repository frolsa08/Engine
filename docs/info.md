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
| `Z` | Comparison flag: 1 when the last CMP found A equal to its operand. |
| `LT` | Unsigned comparison flag: 1 when the last CMP found A less than its operand. |
| `BIT` | Last bit sampled by IN or transmitted by OUT. |
| `FAIL` | Result of the last completed FIFO instruction: 1 for a failed nonblocking attempt, 0 for a successful transfer. |
| Input FIFO | Byte queue into the engine, consumed by PULL. Separate from program memory and A. |
| Output FIFO | Byte queue out of the engine, produced by PUSH. Separate from the GPIO output latch. |

A retains a byte independently of the pin output latch. MOV A,PINS stores an input sample; SHL/SHR operate on that stored byte; MOV PINS,A writes it to the output latch; JNZ tests it. A is useful for data-dependent transfers and input processing, but the constant UART example below does not use it. Arithmetic addition is not required for these functions.

Reset sets PC, A, X, output latch, DIR, and all flags to zero, and empties both FIFOs. All pins are inputs. Execution begins at byte address 0 when reset is released with a program available. Physical asynchronous inputs require synchronization; WAIT and input reads use the resulting digital input values.

### Operand notation

| Operand | Meaning |
| --- | --- |
| `imm8` | An unsigned 8-bit immediate: a literal value encoded directly in the program, from 0 to 255 (`0x00`–`0xFF`). It is not a register or an address to dereference. |
| `addr8` | An unsigned 8-bit opcode byte address used as a branch target. |
| `pin` | GPIO index, 0–7; its use as input or output depends on the instruction. |
| `level` | Required input level, 0 or 1. |
| `condition` | One of Z, NZ, LT, GE, BIT, NBIT, FAIL, or OK; encoded in the BR opcode. |
| `NB` | Nonblocking FIFO mode, selected by a distinct opcode; it occupies no operand byte. |

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
| `0x14` | `PULL A` | 1 | Read and remove one byte from the input FIFO into A; set FAIL=0. If empty, stall until a byte is available. |
| `0x15` | `PUSH A` | 1 | Write A to the output FIFO; set FAIL=0 and retain A. If full, stall until space is available. |
| `0x16` | `PULL A, NB` | 1 | Attempt to read and remove one byte into A. On success set FAIL=0; if empty, retain A, set FAIL=1, and continue. |
| `0x17` | `PUSH A, NB` | 1 | Attempt to write A to the output FIFO. On success set FAIL=0; if full, enqueue nothing, set FAIL=1, and continue. Retain A. |
| `0x20` | `SET A, imm8` | 2 | Load A. |
| `0x21` | `AND A, imm8` | 2 | Bitwise AND A with the following byte. |
| `0x22` | `XOR A, imm8` | 2 | XOR A with the immediate. |
| `0x23` | `SHL A` | 1 | Shift left; fill bit0 with zero and discard bit7. |
| `0x24` | `SHR A` | 1 | Shift right; fill bit7 with zero and discard bit0. |
| `0x25` | `SET X, imm8` | 2 | Load X. |
| `0x26` | `CMP A, imm8` | 2 | Set Z=(A == imm8) and LT=(A < imm8), using unsigned comparison; retain A. |
| `0x30–0x3F` | `WAIT pin, level` | 1 | Hold PC until the selected input equals the selected level. |
| `0x40` | `DELAY imm8` | 2 | Stall for 0–255 extra clocks after reading the operand. |
| `0x50` | `JMP addr8` | 2 | Jump to an opcode byte address. |
| `0x51` | `JNZ A, addr8` | 2 | Jump if A is nonzero. |
| `0x52` | `LOOP X, addr8` | 2 | Decrement X modulo 256; jump if the result is nonzero. |
| `0x60–0x67` | `IN pin, 1` | 1 | Sample the selected input into BIT, then set A=(A >> 1) \| (BIT << 7). |
| `0x68–0x6F` | `OUT pin, 1` | 1 | Copy the old A[0] to BIT and the selected output-latch bit, then set A=A >> 1 with zero fill. |
| `0x70–0x77` | `SETBIT pin` | 1 | Set the selected output-latch bit; retain all other bits. |
| `0x78–0x7F` | `CLRBIT pin` | 1 | Clear the selected output-latch bit; retain all other bits. |
| `0x80–0x87` | `DRIVE pin` | 1 | Set the selected DIR bit; retain other direction bits and the output latch. |
| `0x88–0x8F` | `RELEASE pin` | 1 | Clear the selected DIR bit; retain other direction bits and the output latch. |
| `0x90–0x97` | `BR condition, addr8` | 2 | If the encoded condition is true, jump to the following byte address; otherwise continue after the operand. Retain flags. |

For WAIT, `opcode = 0x30 | (level << 3) | pin`, where level is 0 or 1 and pin is 0–7. For example, `WAIT 5, 1` encodes as `0x3D`. WAIT tests a level; waiting for a transition requires waiting for the opposite level first.

SET PINS and MOV PINS update all eight output-latch bits; DIR determines which bits physically drive pins. LOOP with initial X=0 wraps to 255 on its first decrement and runs 256 iterations in the usual counter loop.

#### Bit operations

For IN, OUT, SETBIT, CLRBIT, DRIVE, and RELEASE, the low three opcode bits encode pin. The respective opcode bases are `0x60`, `0x68`, `0x70`, `0x78`, `0x80`, and `0x88`: `opcode = base | pin`. For example, IN 5,1 is `65`; OUT 0,1 is `68`; SETBIT 3 is `73`; DRIVE 0 is `80`.

The literal 1 in IN and OUT means exactly one bit; it is not an operand byte. This base version supports only right shifts. Eight IN operations receive an LSB-first byte into A; eight OUT operations transmit an LSB-first byte and leave A=0. A single IN retains seven old bits, so clear A first when only one sampled bit is wanted.

OUT updates BIT, A, and the selected output-latch bit on the same execution edge. It does not change DIR. SETBIT and CLRBIT also change only the latch; a pin physically drives that value only while its DIR bit is 1. DRIVE enables the previously latched value. For open-drain-style operation, use CLRBIT before DRIVE, and RELEASE to return the line to an input; an external pull-up supplies HIGH.

#### Flags and conditional branches

BR uses `opcode = 0x90 | condition_code`, followed by addr8:

| Condition code | Opcode | Condition | Test |
| --- | --- | --- | --- |
| `0` | `0x90` | `Z` | Z=1: equal. |
| `1` | `0x91` | `NZ` | Z=0: not equal. |
| `2` | `0x92` | `LT` | LT=1: unsigned less than. |
| `3` | `0x93` | `GE` | LT=0: unsigned greater than or equal. |
| `4` | `0x94` | `BIT` | BIT=1. |
| `5` | `0x95` | `NBIT` | BIT=0. |
| `6` | `0x96` | `FAIL` | FAIL=1: the last FIFO attempt failed. |
| `7` | `0x97` | `OK` | FAIL=0: the last FIFO transfer succeeded. |

Only CMP changes Z and LT. Only IN and OUT change BIT. Completed PULL and PUSH operations change FAIL. All other instructions retain these flags. Evaluate a result before another instruction overwrites its corresponding flag. BR NZ tests Z; the existing JNZ A tests A directly. For example, CMP A,0xD5 encodes as `26 D5`, and BR Z,0x20 as `90 20`.


The following standalone program demonstrates FIFO status, equality, unsigned comparison, and GPIO decisions. GPIO0 indicates A=0x55, GPIO1 indicates another value below 0x80, GPIO2 indicates a value at or above 0x80, and GPIO3 indicates an unavailable FIFO transfer. The original byte is retained for the output FIFO. Flags and the queues are the only inputs to these decisions.

```asm
SET PINS, 0x00
SET DIR, 0x0F

PULL A, NB
BR FAIL, fifo_error      ; No byte: A was not overwritten.
CMP A, 0x55
BR Z, equal
CMP A, 0x80
BR LT, below

SETBIT 2
JMP send

below:
SETBIT 1
JMP send

equal:
SETBIT 0

send:
PUSH A, NB
BR FAIL, fifo_error
HALT

fifo_error:
SETBIT 3
HALT
```

Labels denote opcode byte addresses; they are resolved during assembly and occupy no program bytes. Each CMP and BR takes two clocks. SETBIT retains the comparison flags. This example occupies **28 bytes** and needs no timer or interrupt.

#### FIFO transfers

FIFO directions are relative to the engine: input data is consumed by PULL; output data is produced by PUSH. FIFO capacity and host access are implementation parameters, not encoded by these instructions. FIFOs carry data bytes, not program instructions or GPIO history. Loading program memory and controlling execution use a separate host interface.

A successful transfer moves exactly one byte on its completion edge. Blocking PULL/PUSH hold PC, A, X, flags, output latch, and DIR while waiting; external producers and consumers can still update the queues. Nonblocking instructions always finish in one clock. They leave the queue unchanged if the attempted transfer fails. Successful blocking and nonblocking instructions set FAIL=0.

For a transmitter that can remain idle until data arrives, use PULL A. Use PULL A,NB when the program must handle other work if no byte is available. Use PUSH A,NB when waiting would disrupt input sampling; the program must handle FAIL by reporting, retrying, or discarding data according to its protocol.

### Timing

A single-byte instruction takes one clock unless WAIT or a blocking FIFO transfer stalls. A two-byte instruction takes two: read the opcode first, then read the operand and apply the operation. Unless branching, PC advances by the instruction length. WAIT keeps PC fixed until its condition matches. A matching WAIT or a FIFO transfer that can complete immediately takes one clock. BR takes two clocks whether or not its branch is taken.

DELAY occupies `2 + imm8` clocks. DELAY 0 still occupies its two instruction clocks. A following instruction begins after those clocks. All output changes occur on core-clock rising edges.

This timing profile assumes one instruction byte is available each clock, without hidden fetch stalls. An RTL implementation with additional memory/fetch cycles must define a different timing profile and adjust program delays accordingly.

HALT is distinct from reset: it preserves driven levels. Program execution must not fall through past the loaded image. Branches must stay within it; a program must not depend on PC wraparound.

### What these instructions can do

- Generate finite digital waveforms, pulses, and repetitive patterns.
- Generate UART TX frames using output writes and timed holds.
- Generate SPI clock/data/chip-select patterns; read inputs at programmed points.
- Shift serial data into or out of A, and change individual GPIO bits without rewriting the whole port.
- Receive externally clocked bytes, such as the data portion of a PS/2 frame, using WAIT and IN.
- Exchange bytes with the host or another connected data source/sink through FIFOs; handle unavailable transfers with NB and BR.
- Mask input samples with AND and compare protocol fields using CMP and BR.
- Synchronize execution to an input level or transition using WAIT.
- Repeat short sequences using X and LOOP, or react to sampled data using A and JNZ.
- Release a pin by clearing its DIR bit. Driving an open-drain-style line low requires its output latch to be zero; releasing it requires DIR=0 and an external pull-up.

Protocol framing, bit order, sampling points, and error handling are program responsibilities. These primitives do not automatically provide a complete UART receiver, SPI peripheral, or I²C controller. They do not guarantee transitions on every clock while two-byte instructions execute. Periodic timing, edge timestamps, phase recovery, CRC acceleration, and automatic FIFO transfers are not part of this base version; complete 10BASE-T, CAN, and USB Low Speed support requires further design and timing verification.

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


### Example: UART RX, one byte, 8N1

Use the same 50 MHz core and 434-clock bit interval as the UART TX example. GPIO0 is RX; GPIO1 is an output that reports an output-FIFO overflow. Other pins remain inputs. This program receives one byte, LSB first, and attempts to return it through the engine's output FIFO.

The start condition is observed through synchronized GPIO0. Offsets below are relative to the clock when WAIT 0,0 completes, rather than to the physical input edge. The program checks the start level halfway through the nominal start bit, samples eight data bits at their centers, and waits for HIGH at the nominal stop-bit center.

```asm
SET PINS, 0x00
SET DIR, 0x02          ; GPIO0 input; GPIO1 overflow indicator.
SET A, 0

start:
WAIT 0, 1             ; Establish idle before looking for a start.
WAIT 0, 0
DELAY 214
IN 0, 1               ; Start-level check at offset 217 clocks.
BR BIT, start         ; HIGH: reject the candidate start.

SET A, 0
SET X, 8
DELAY 255
DELAY 168

data:
IN 0, 1               ; Shift one received bit into A.
DELAY 255
DELAY 172
LOOP X, data

WAIT 0, 1             ; Expected stop level, without modifying A.
PUSH A, NB
BR FAIL, overflow
HALT

overflow:
SETBIT 1
HALT
```

The first data sample occurs 651 clocks after the detected start. Subsequent data samples are separated by:

```text
DELAY 255: 257 clocks
DELAY 172: 174 clocks
LOOP X:      2 clocks
next IN:     1 clock
total:     434 clocks
```

| Sample | Offset, clocks | Meaning |
| --- | ---: | --- |
| Start check | 217 | Must be LOW. |
| Data0 | 651 | A receives the least-significant bit first. |
| Data1 | 1085 | Second data bit. |
| Data2 | 1519 | Third data bit. |
| Data3 | 1953 | Fourth data bit. |
| Data4 | 2387 | Fifth data bit. |
| Data5 | 2821 | Sixth data bit. |
| Data6 | 3255 | Seventh data bit. |
| Data7 | 3689 | A now contains the complete byte. |
| Stop-level wait | 4123 | Completes here if RX is HIGH. |

With the TX waveform above, A becomes 0x55. The program occupies **35 bytes**. PUSH A,NB avoids blocking the sampling path; on overflow the byte is discarded and GPIO1 becomes HIGH.

This is a single-frame example. WAIT at the stop point preserves A but does not diagnose a framing error: if RX is LOW, it waits until a later HIGH and may then accept the byte. There is no timeout, parity, break detection, or continuous-stream guarantee. Input synchronization latency and transmitter clock error must be included in a real receiver's sampling budget.

### Example: SPI controller TX, 0x55, mode 0

Use the same 50 MHz timing profile. GPIO0 is SCK, GPIO1 is MOSI, and GPIO2 is active-low CS. Other pins remain inputs. This example sends one byte MSB first; it does not receive MISO.

Mode 0 uses idle-LOW SCK, sampling on rising edges and changing data during the LOW phase. See the [Microchip SPI mode definitions](https://onlinedocs.microchip.com/oxy/GUID-A299F4E7-F38C-4DF5-96C0-A87B9F519156-en-US-4/GUID-8A5B8750-B99E-4176-834E-E44E98F4A098.html).

OUT shifts right, so the constant loaded into A is bit-reversed: 0xAA produces the MSB-first wire sequence for 0x55. For variable MSB-first data, the host can reverse each byte before placing it in the input FIFO, and PULL A can replace SET A,0xAA.

```asm
SET PINS, 0x04        ; CS HIGH, SCK LOW, MOSI LOW.
SET DIR, 0x07
SET A, 0xAA           ; Bit-reversed 0x55.
SET X, 8

CLRBIT 2              ; Assert CS.
DELAY 22

bit:
OUT 1, 1              ; Put the next bit on MOSI.
DELAY 19
SETBIT 0              ; Rising SCK: target samples MOSI.
DELAY 22
CLRBIT 0              ; Falling SCK.
LOOP X, bit

DELAY 22
SETBIT 2              ; Deassert CS after the last falling edge.
HALT
```

| Interval | Clocks | Time at 50 MHz |
| --- | ---: | ---: |
| MOSI update to rising SCK | (2+19)+1 = 22 | 440 ns |
| SCK HIGH | (2+22)+1 = 25 | 500 ns |
| SCK LOW between bits | LOOP 2 + OUT 1 + DELAY 21 + SETBIT 1 = 25 | 500 ns |
| SCK period | 50 | 1 us, or 1 MHz |
| Final falling SCK to CS HIGH | LOOP 2 + DELAY 24 + SETBIT 1 = 27 | 540 ns |

The eight rising edges sample MOSI as 0,1,0,1,0,1,0,1. The program occupies **24 bytes**. HALT leaves CS HIGH and SCK LOW.

A is the only data register in this base ISA. Alternating OUT and IN on A would shift it twice and corrupt a simultaneous transfer. General full-duplex SPI therefore needs a separate receive/transmit register, another coordinated engine, or a different program/data strategy.

### Example: I2C controller write, address 0x50, data 0x55

Use the same 50 MHz core. GPIO0 is SCL, GPIO1 is SDA, GPIO2 is an undriven scratch output-latch bit, and GPIO3 is a NACK indicator. SCL and SDA require external pull-ups; their output-latch bits stay zero. DRIVE pulls a line LOW, and RELEASE allows its pull-up to raise it.

This single-controller example sends START, the address byte 0xA0 (7-bit address 0x50 plus write=0), one data byte 0x55, and STOP. It samples the target's ACK after each byte. Each clock release is followed by WAIT SCL,HIGH, so a target may stretch the LOW phase. START, STOP, ACK, and open-drain signaling follow the [NXP I2C specification](https://www.nxp.com/docs/en/user-guide/UM10204.pdf).

The transmitted constants are bit-reversed for right-shifting OUT: 0x05 for address byte 0xA0, and 0xAA for data byte 0x55. OUT 2,1 extracts the next bit into BIT without driving GPIO2; BR BIT then chooses whether to release SDA or drive it LOW.

```asm
SET PINS, 0x00        ; Latches for SCL and SDA remain LOW.
SET DIR, 0x08         ; Only the NACK indicator is driven.
WAIT 0, 1
WAIT 1, 1
DELAY 248             ; Bus-free interval.

DRIVE 1               ; START: SDA falls while SCL is HIGH.
DELAY 248
DRIVE 0               ; Begin the first SCL LOW phase.

SET A, 0x05           ; Bit-reversed address byte 0xA0.
SET X, 8

address_bit:
OUT 2, 1              ; Extract a bit; GPIO2 remains an input.
BR BIT, address_one
DRIVE 1
JMP address_clock
address_one:
RELEASE 1
NOP
NOP

address_clock:
DELAY 248
RELEASE 0
WAIT 0, 1             ; Allow clock stretching.
DELAY 248
DRIVE 0
LOOP X, address_bit

RELEASE 1             ; Release SDA for address ACK.
DELAY 248
RELEASE 0
WAIT 0, 1
DELAY 123
IN 1, 1               ; BIT=0 means ACK; A is no longer needed.
DELAY 122
DRIVE 0
BR BIT, nack

SET A, 0xAA           ; Bit-reversed data byte 0x55.
SET X, 8

data_bit:
OUT 2, 1
BR BIT, data_one
DRIVE 1
JMP data_clock
data_one:
RELEASE 1
NOP
NOP

data_clock:
DELAY 248
RELEASE 0
WAIT 0, 1
DELAY 248
DRIVE 0
LOOP X, data_bit

RELEASE 1             ; Release SDA for data ACK.
DELAY 248
RELEASE 0
WAIT 0, 1
DELAY 123
IN 1, 1
DELAY 122
DRIVE 0
BR BIT, nack
JMP stop

nack:
SETBIT 3              ; Report NACK, then issue STOP.

stop:
DRIVE 1               ; Prepare SDA LOW while SCL is LOW.
DELAY 248
RELEASE 0
WAIT 0, 1
DELAY 248
RELEASE 1             ; STOP: SDA rises while SCL is HIGH.
DELAY 248             ; Bus-free interval before HALT.
HALT
```

Both branches selecting an SDA bit occupy three clocks after BR: DRIVE+JMP or RELEASE+NOP+NOP. Thus transmitted zeros and ones have the same SCL timing.

With ideal instantaneous pull-up edges and no stretching:

| Interval | Clocks | Time at 50 MHz |
| --- | ---: | ---: |
| Data-clock HIGH | WAIT 1 + DELAY 250 + DRIVE 1 = 252 | 5.04 us |
| Data-clock LOW between data bits | LOOP 2 + OUT 1 + BR 2 + selection 3 + DELAY 250 + RELEASE 1 = 259 | 5.18 us |
| Data-clock period | 511 | About 97.85 kHz |
| ACK-clock HIGH | WAIT 1 + DELAY 125 + IN 1 + DELAY 124 + DRIVE 1 = 252 | 5.04 us |

START hold, STOP setup, and the programmed bus-free delay are each at least 250 clocks, or 5 us. Pull-up rise time, synchronization, and stretching can lengthen the intervals. This is a conservative Standard-mode timing example, not a fixed 100 kHz clock.

The program occupies **96 bytes**. On ACK for both bytes, GPIO3 stays LOW. On either NACK, it becomes HIGH and the program sends STOP. HALT releases SCL and SDA.

This example assumes a free bus and one controller. It does not implement arbitration, repeated START, reads, bus recovery, or a timeout for stuck/stretched lines. GPIO2 must remain undriven and unused by another task. Pull-ups and pin electrical compatibility must satisfy the external interface requirements.

## Current RTL status


## How to test the current RTL

Run `make` from the `test` directory. The supplied description says the existing Cocotb test checks that inputs 20 and 30 produce an output of 50. That test does not validate this ISA or the UART program.

The new ASM examples were checked with a software model of the specified instruction timing: branch paths and byte addresses, all 256 UART RX byte values and FIFO overflow, SPI bit order and clock intervals, and I2C ACK/NACK and clock stretching. These checks do not validate RTL, asynchronous input synchronization, or analog rise times.

## External hardware
