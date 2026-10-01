"""SPI host-interface agent template.

Pin mapping, SPI mode, and transaction framing are intentionally pending the
RTL host-interface contract.
"""


class MasterIfAgent:
    def __init__(self, dut):
        self.dut = dut

    async def write_program(self, address, data):
        """Write program bytes over the host SPI interface."""
        raise NotImplementedError("Define SPI pins and program-load framing first")


class MasterIfMonitor:
    async def run(self, publish):
        """Decode observed SPI transactions and publish them to the scoreboard."""
        raise NotImplementedError("Define SPI pins and transaction framing first")
