# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# test_my_design.py (extended)

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge,RisingEdge
from queue import Queue
from cocotb.simulator import *

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
        await RisingEdge(dut.rstn_i)
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
    

class mon_data_t:
    def __init__(self):
        self.data = 0
        self.data_id = 0
  
  
class chnl_monitor:
    def __init__(self, ch_id, name="chnl_monitor"):
        self.ch_id = ch_id
        self.name = name
        self.mon_mb = Queue()
    
    async def run(self, dut):
        await self.mon_trans(dut)

    async def mon_trans(self, dut):
        while True:
            m = mon_data_t()
            await RisingEdge(dut.clk_i)
            if self.ch_id == 0:       
                while str(dut.inst_slva_fifo_0.chx_valid_i.value) != '1' or str(dut.inst_slva_fifo_0.chx_ready_o.value) != '1':
                    await RisingEdge(dut.clk_i)
                m.data = dut.inst_slva_fifo_0.chx_data_i.value
            elif self.ch_id == 1:
                while str(dut.inst_slva_fifo_1.chx_valid_i.value) != '1' or str(dut.inst_slva_fifo_1.chx_ready_o.value) != '1':
                    await RisingEdge(dut.clk_i)
                m.data = dut.inst_slva_fifo_1.chx_data_i.value
            elif self.ch_id == 2:
                while str(dut.inst_slva_fifo_2.chx_valid_i.value) != '1' or str(dut.inst_slva_fifo_2.chx_ready_o.value) != '1':
                    await RisingEdge(dut.clk_i)
                m.data = dut.inst_slva_fifo_2.chx_data_i.value
            self.mon_mb.put(m)
            
            time_ns = get_sim_time()
            dut._log.info("%s %s monitored channle data %8x", time_ns, self.name, m.data)
            

class mcdt_monitor:
    def __init__(self, name="mcdt_monitor"):
        self.name = name
        self.mon_mb = Queue()
    
    async def run(self, dut):
        await self.mon_trans(dut);

    async def mon_trans(self, dut):
        while True:
            m = mon_data_t()
            await RisingEdge(dut.clk_i)
            while(dut.inst_arbiter.data_val_o.value != 1):
                await RisingEdge(dut.clk_i)
            
            m.data = dut.inst_arbiter.arb_data_o.value
            m.data_id = dut.inst_arbiter.arb_id_o.value
            self.mon_mb.put(m)
            time_ns = get_sim_time()
            dut._log.info("%s %s monitored mcdt data %8x and id %0d", time_ns, self.name, m.data, m.data_id)
            

class chnl_checker:
    def __init__(self, name="chnl_checker"):
        self.name = name
        self.error_count = 0
        self.cmp_count = 0
        self.in_mbs = [Queue(), Queue(), Queue()]
        self.out_mb = Queue()
         
         
    async def run(self, dut):
        await self.do_compare(dut)


    async def do_compare(self, dut):
        im = mon_data_t()
        om = mon_data_t()
        while True:
            while self.out_mb.empty():
                await RisingEdge(dut.clk_i)
            om = self.out_mb.get();
            if om.data_id == 0 or om.data_id == 1 or om.data_id == 2:
                while self.in_mbs[om.data_id].empty():
                    await RisingEdge(dut.clk_i)
                im = self.in_mbs[om.data_id].get();
            else: 
                dut._log.info("id %0d is not available", om.data_id)   
                    
            if om.data != im.data:
                self.error_count = self.error_count + 1;
                dut._log.info("[CMPFAIL] Compared failed! mcdt out data %8x ch_id %0d is not equal with channel in data %8x", om.data, om.data_id, im.data)
            else:
                dut._log.info("[CMPSUCD] Compared succeeded! mcdt out data %8x ch_id %0d is equal with channel in data %8x", om.data, om.data_id, im.data)

            self.cmp_count = self.cmp_count + 1;

     
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


class chnl_root_test:
    def __init__(self, name = "chnl_root_test"):
        self.name = name
        self.drivers = [driver(0), driver(1), driver(2)]
        self.monitors = [chnl_monitor(0, "chnl_monitor0"), chnl_monitor(1, "chnl_monitor1"), chnl_monitor(2, "chnl_monitor2")]
        self.mcdt_mon = mcdt_monitor()
        self.chker = chnl_checker()
        for i in range(3):
            self.monitors[i].mon_mb = self.chker.in_mbs[i]
        self.mcdt_mon.mon_mb = self.chker.out_mb       
        

    async def run(self, dut): 
        for driver_i in self.drivers:
            await cocotb.start(driver_i.run(dut))
        for monitor_i in self.monitors:
            await cocotb.start(monitor_i.run(dut))
        await cocotb.start(self.mcdt_mon.run(dut))
        await cocotb.start(self.chker.run(dut))
        dut._log.info("%s instantiated and connected objects", self.name)
     
     

@cocotb.test()
async def my_first_test(dut):
    """Try accessing the design."""

    await cocotb.start(generate_clock(dut))  # run the clock "in the background"
    await cocotb.start(generate_rst(dut))  # run the clock "in the background"
    
    
    
    test = chnl_root_test()
    await cocotb.start(test.run(dut))
    
    dut._log.info("***************** finished********************")
    
    time_ns = get_sim_time()
    dut._log.info("%s", time_ns)
    # await Timer(5, units="ns")  # wait a bit
    await RisingEdge(dut.rstn_i)
    for cycle in range(80):
        await RisingEdge(dut.clk_i)
        # dut._log.info("ch0_data_i is %s", dut.inst_slva_fifo_0.chx_data_i.value)
        # dut._log.info("ch0_data_i is %s", dut.inst_slva_fifo_0.chx_data_i.value)
        # dut._log.info("ch1_data_i is %s", dut.inst_slva_fifo_1.chx_data_i.value)
        # dut._log.info("ch2_data_i is %s", dut.inst_slva_fifo_2.chx_data_i.value)
        # dut._log.info("slvx_data_o is %s", dut.inst_slva_fifo_0.slvx_data_o.value)
        # dut._log.info("slv0_data_i is %s", dut.inst_arbiter.slv0_data_i.value)
        # dut._log.info("mcdt_data_o is %s\n", dut.mcdt_data_o.value)
    # await FallingEdge(dut.clk_i)  # wait for falling edge/"negedge"

    # dut._log.info("my_signal_1 is %s", dut.mcdt_data_o.value)
    # assert dut.my_signal_2.value[0] == 0, "my_signal_2[0] is not 0!"
    # clk_gen.kill()