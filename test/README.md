# Sample testbench for a Tiny Tapeout project

This testbench uses [cocotb](https://docs.cocotb.org/en/stable/) to drive the DUT and check the outputs.
The active Cocotb tests are in `tb/tests.py`, selected by `COCOTB_TEST_MODULES = tb.tests` in the Makefile.
See the [Tiny Tapeout testing guide](https://tinytapeout.com/hdl/testing/) for more information.

## Setting up

1. Edit [Makefile](Makefile) and modify `PROJECT_SOURCES` to point to your Verilog files.
2. Edit [tb.v](tb.v) to connect the design under test to the testbench signals.

## Install test dependencies

On Debian/Ubuntu, install the simulator and Python virtual environment support:

```sh
sudo apt update
sudo apt install python3.12-venv iverilog
```

From this `test` directory, create and activate a virtual environment, then install the Python dependencies:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Keep the virtual environment activated when running the tests. In a new terminal, activate it again with `. .venv/bin/activate`.

## How to run

To run the RTL simulation while the virtual environment is active:

```sh
make -B
```

To run gatelevel simulation, first harden your project and copy `../runs/wokwi/results/final/verilog/gl/{your_module_name}.v` to `gate_level_netlist.v`.

Then run:

```sh
make -B GATES=yes
```

If you wish to save the waveform in VCD format instead of FST format, edit tb.v to use `$dumpfile("tb.vcd");` and then run:

```sh
make -B FST=
```

This will generate `tb.vcd` instead of `tb.fst`.

## Clean generated files

From this `test` directory, run:

```sh
make clean
```

This works even when the virtual environment is not active. It removes the entire `sim_build` directory (RTL and gate-level builds), Cocotb's `results.xml`, and the `tb.fst` or `tb.vcd` waveform. It keeps `.venv` and source files so the test environment is ready for the next run.

If Make reports `Makefile:...: /Makefile.sim: No such file or directory`, Cocotb is not available in the active Python environment. Activate `.venv` and install the test dependencies with `python -m pip install -r requirements.txt`. If `python3 -m venv .venv` fails because `ensurepip` is missing, install `python3.12-venv` and recreate the virtual environment.

## How to view the waveform file

Using GTKWave

```sh
gtkwave tb.fst tb.gtkw
```

Using Surfer

```sh
surfer tb.fst
```
