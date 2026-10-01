"""Cycle-level comparison between monitor events and the golden model."""


class Scoreboard:
    def __init__(self, golden_model):
        self.golden_model = golden_model
        self.events = []

    def publish(self, event):
        """Receive a cycle-indexed event from an agent monitor."""
        self.events.append(event)

    def check_cycle(self, cycle, gpio_input, observed_output, observed_oe):
        """Advance the model and compare pin value and output-enable mask."""
        raise NotImplementedError("Define event ordering and model output comparison")