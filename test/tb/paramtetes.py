"""PIO opcode definitions matching the current draft in docs/info.md."""

NOP = 0x00
MOV_A_PINS = 0x10
MOV_PINS_A = 0x11
SET_PINS_IMM = 0x12
SET_DIR_IMM = 0x13
SET_A_IMM = 0x20
ADD_A_IMM = 0x21
XOR_A_IMM = 0x22
SHL_A = 0x23
SHR_A = 0x24
SET_X_IMM = 0x25
WAIT_BASE = 0x30
DELAY = 0x40
JMP = 0x50
JNZ_A = 0x51
LOOP_X = 0x52

_TWO_BYTE_OPCODES = {
    SET_PINS_IMM,
    SET_DIR_IMM,
    SET_A_IMM,
    ADD_A_IMM,
    XOR_A_IMM,
    SET_X_IMM,
    DELAY,
    JMP,
    JNZ_A,
    LOOP_X,
}


def instruction_length(opcode):
    """Return instruction size in bytes; WAIT encodes its fields in the opcode."""
    if opcode in _TWO_BYTE_OPCODES:
        return 2
    if opcode in (NOP, MOV_A_PINS, MOV_PINS_A, SHL_A, SHR_A):
        return 1
    if opcode & 0xF0 == WAIT_BASE:
        return 1
    raise ValueError(f"Unsupported opcode: 0x{opcode:02x}")


def encode_wait(pin, level):
    """Encode WAIT pin, level into its single opcode byte."""
    if not 0 <= pin < 8 or level not in (0, 1):
        raise ValueError("WAIT requires pin 0-7 and level 0 or 1")
    return WAIT_BASE | (level << 3) | pin