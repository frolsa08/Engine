## How it works

The design adds the 8-bit value on `ui_in` to the 8-bit value on `uio_in` and places the 8-bit result on `uo_out`. Any carry beyond bit 7 is discarded. The bidirectional pins are not driven, and the clock, reset, and enable inputs are unused.

## How to test

Run `make` from the `test` directory. The Cocotb test applies 20 and 30 to the inputs and checks that the output is 50.

## External hardware

No external hardware is required.
