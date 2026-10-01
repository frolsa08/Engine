# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


@cocotb.test()
async def test_8_bit_adder(dut):
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    test_vectors = ((0, 0, 0), (20, 30, 50), (255, 1, 0), (200, 100, 44))
    for lhs, rhs, expected in test_vectors:
        dut.ui_in.value = lhs
        dut.uio_in.value = rhs
        await Timer(1, unit="ns")
        assert int(dut.uo_out.value) == expected
