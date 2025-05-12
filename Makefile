# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# Makefile

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/hdl1/arbiter.v
VERILOG_SOURCES += $(PWD)/hdl1/slave_fifo.v
VERILOG_SOURCES += $(PWD)/hdl1/mcdt.v
# use VHDL_SOURCES for VHDL files

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = mcdt

# MODULE is the basename of the Python test file
MODULE = tb

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

cleanall:
	rm -rf sim_build __pycache__ *.xml
