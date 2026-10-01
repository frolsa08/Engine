"""High-level PIO scenario templates; interface details are still pending."""


async def load_program(master_if, program):
    """Load a sequence of bytes at address zero using the SPI master agent."""
    for address, value in enumerate(program):
        await master_if.write_program(address, value)


async def wait_for_gpio_level(gpio, pin, level):
    """Drive/observe a GPIO transition for a WAIT instruction scenario."""
    raise NotImplementedError("Define GPIO monitor events and resolved-pin behavior")