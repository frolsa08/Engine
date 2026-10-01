"""GPIO stimulus and observation agent template."""


class GpioAgent:
    def __init__(self, dut):
        self.dut = dut

    async def drive_inputs(self, value):
        """Drive the externally supplied GPIO input value."""
        self.dut.uio_in.value = value & 0xFF


class GpioMonitor:
    async def run(self, publish):
        """Sample GPIO values and output enables on active clock edges."""
        raise NotImplementedError("Add edge sampling and pin-resolution policy")