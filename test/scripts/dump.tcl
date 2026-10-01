# Run the Cocotb testbench with Verilator's FST tracing enabled.
# Invoke from any directory with: tclsh path/to/test/scripts/dump.tcl
# Additional make targets or variables may be passed as arguments.

set script_dir [file dirname [file normalize [info script]]]
set test_dir [file normalize [file join $script_dir ..]]
set env(PWD) $test_dir

foreach tool {make verilator cocotb-config} {
	if {[auto_execok $tool] eq ""} {
		puts stderr "Required tool not found: $tool"
		exit 1
	}
}

set command [list make -C $test_dir SIM=verilator EXTRA_ARGS=--trace-fst]
lappend command {*}$argv

if {[catch {exec {*}$command 2>@1} output]} {
	puts stderr $output
	exit 1
}

if {$output ne ""} {
	puts -nonewline $output
}
