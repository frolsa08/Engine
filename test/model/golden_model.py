"""Cycle-accurate architectural reference model template for the PIO engine."""

from dataclasses import dataclass, field


@dataclass
class ModelOutput:
    pins: int = 0
    output_enable: int = 0


@dataclass
class PioGoldenModel:
    program: bytearray = field(default_factory=lambda: bytearray(256))
    pc: int = 0
    accumulator: int = 0
    loop_counter: int = 0
    output_latch: int = 0
    direction: int = 0

    def reset(self):
        """Reset architectural state; program-memory reset behavior is TBD."""
        self.pc = 0
        self.accumulator = 0
        self.loop_counter = 0
        self.output_latch = 0
        self.direction = 0

    def load_program_byte(self, address, value):
        self.program[address & 0xFF] = value & 0xFF

    def step(self, gpio_input):
        """Execute one active clock edge and return expected GPIO outputs."""
        raise NotImplementedError("Implement cycle ordering from the finalized ISA")