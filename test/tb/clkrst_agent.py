"""Clock/reset agent interface; replace the TODOs with the supplied implementation."""


class ClkRstAgent:
    def __init__(self, dut):
        self.dut = dut

    async def start_clock(self):
        """Start the configured test clock."""
        raise NotImplementedError("Insert the project clock driver")

    async def apply_reset(self):
        """Apply reset using the polarity and timing defined by the DUT."""
        raise NotImplementedError("Insert the project reset sequence")


class ClkRstMonitor:
    async def run(self, publish):
        """Publish reset and active-clock-edge events to the environment."""
        raise NotImplementedError("Add passive clock/reset observation")