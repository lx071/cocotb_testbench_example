# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# test_my_design.py (extended)

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge,RisingEdge


class chnl_trans:
    def __init__(self, ch_id, pkt_id):
        self.ch_id = ch_id
        self.pkt_id = pkt_id
        self.data_nidles = 0
        self.pkt_nidles = 1
        self.data_size = 10
        
        data = [1] * self.data_size
        for i in range(len(data)):
            data[i] = 0xC000_0000 + (self.ch_id<<24) + (self.pkt_id<<8) + i;
        self.data = data
        
    def set_pkt_id(self, pkt_id):
        self.pkt_id = pkt_id
        data = [1] * self.data_size
        for i in range(len(data)):
            data[i] = 0xC000_0000 + (self.ch_id<<24) + (self.pkt_id<<8) + i;
        self.data = data
     
    def set_data_nidles(self, data_nidles):
        self.data_nidles = data_nidles
        
    def set_pkt_nidles(self, pkt_nidles):
        self.pkt_nidles = pkt_nidles


class driver:
    def __init__(self, ch_id):
        self.ch_id = ch_id
    
    async def run(self, dut):
        if self.ch_id == 0:
            t = chnl_trans(0, 0);
        elif self.ch_id == 1:
            t = chnl_trans(1, 0);
        elif self.ch_id == 2:
            t = chnl_trans(2, 0);
        # t.set_data_nidles(1);
        await cocotb.start(self.chnl_write(dut, t))


    async def chnl_write(self, dut, t):
        num = len(t.data)
        for i in range(num):
            await RisingEdge(dut.clk_i)
            if t.ch_id == 0:
                dut.ch0_valid_i.value = 1
                dut.ch0_data_i.value = t.data[i];
                await FallingEdge(dut.clk_i)
                while dut.ch0_ready_o != 1:
                    await RisingEdge(dut.clk_i)
            elif t.ch_id == 1:
                dut.ch1_valid_i.value = 1
                dut.ch1_data_i.value = t.data[i];
                await FallingEdge(dut.clk_i)
                while dut.ch1_ready_o != 1:
                    await RisingEdge(dut.clk_i)
            elif t.ch_id == 2:
                dut.ch2_valid_i.value = 1
                dut.ch2_data_i.value = t.data[i];
                await FallingEdge(dut.clk_i)
                while dut.ch2_ready_o != 1:
                    await RisingEdge(dut.clk_i)
            
            for i in range(t.data_nidles):
                await self.chnl_idle(dut, t)
        for i in range(t.pkt_nidles):
            await self.chnl_idle(dut, t)

        
    async def chnl_idle(self, dut, t):
        await RisingEdge(dut.clk_i)
        if t.ch_id == 0:
            dut.ch0_valid_i.value = 0
            dut.ch0_data_i.value = 0
        elif t.ch_id == 1:
            dut.ch1_valid_i.value = 0
            dut.ch1_data_i.value = 0
        elif t.ch_id == 2:
            dut.ch2_valid_i.value = 0
            dut.ch2_data_i.value = 0
        
        
async def generate_clock(dut):
    """Generate clock pulses."""
    dut.clk_i.value = 0
    for cycle in range(100):
        dut.clk_i.value = 0
        await Timer(5, units="ns")
        dut.clk_i.value = 1
        await Timer(5, units="ns")


async def generate_rst(dut):
    await Timer(10, units="ns")
    dut.rstn_i.value = 0
    for cycle in range(10):
        await RisingEdge(dut.clk_i)
    dut.rstn_i.value = 1


@cocotb.test()
async def my_first_test(dut):
    """Try accessing the design."""

    await cocotb.start(generate_clock(dut))  # run the clock "in the background"
    await cocotb.start(generate_rst(dut))  # run the clock "in the background"
    
    await RisingEdge(dut.rstn_i)
    
    drivers = [driver(0), driver(1), driver(2)]
    
    for d in drivers:
        await cocotb.start(d.run(dut))
    
    
    # await Timer(5, units="ns")  # wait a bit
    for cycle in range(40):
        await RisingEdge(dut.clk_i)
        dut._log.info("ch0_data_i is %s", dut.inst_slva_fifo_0.chx_data_i.value)
        dut._log.info("ch1_data_i is %s", dut.inst_slva_fifo_1.chx_data_i.value)
        dut._log.info("ch2_data_i is %s", dut.inst_slva_fifo_2.chx_data_i.value)
        # dut._log.info("slvx_data_o is %s", dut.inst_slva_fifo_0.slvx_data_o.value)
        # dut._log.info("slv0_data_i is %s", dut.inst_arbiter.slv0_data_i.value)
        dut._log.info("mcdt_data_o is %s\n", dut.mcdt_data_o.value)
    # await FallingEdge(dut.clk_i)  # wait for falling edge/"negedge"

    # dut._log.info("my_signal_1 is %s", dut.mcdt_data_o.value)
    # assert dut.my_signal_2.value[0] == 0, "my_signal_2[0] is not 0!"
