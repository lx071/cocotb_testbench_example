# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# test_my_design.py (extended)

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge,RisingEdge
from queue import Queue
from cocotb.simulator import *
# from pyuvm import *


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


class mon_data_t:
    def __init__(self):
        self.data = 0
        self.data_id = 0

     
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


class McdtBfm:
    def __init__(self, dut):
        self.dut = dut
        self.driver_queue = [Queue(maxsize=1), Queue(maxsize=1), Queue(maxsize=1)]
        # self.cmd_mon_queue = Queue(maxsize=0)
        self.mcdt_mon_queue = Queue()
        self.chnl_mon_queue = [Queue(), Queue(), Queue()]
        
    async def send_trans(self, ch_id):
        self.driver_queue[ch_id].put(ch_id)
        
    async def get_result(self):
        result = await self.result_mon_queue.get()
        return result
    
    async def driver_bfm(self, ch_id):
        dut = self.dut
        # self.dut.start <= 0
        # self.dut.A <= 0
        # self.dut.B <= 0
        # self.dut.op <= 0
        await RisingEdge(dut.rstn_i)
        
        while True:
            # await FallingEdge(self.dut.clk)
            await RisingEdge(dut.clk_i)
            # if self.dut.start.value == 0 and self.dut.done.value == 0:

            if self.driver_queue[ch_id].empty() is False:
                ch_id = self.driver_queue[ch_id].get_nowait()
                if ch_id == 0:
                    t = chnl_trans(0, 0);
                elif ch_id == 1:
                    t = chnl_trans(1, 0);
                elif ch_id == 2:
                    t = chnl_trans(2, 0);
                # t.set_data_nidles(1);
                await cocotb.start(self.chnl_write(t))
                # self.dut.start = 1
    
    async def chnl_write(self, t):
        dut = self.dut
        num = len(t.data)
        for i in range(num):
            await RisingEdge(dut.clk_i)
            time_ns = get_sim_time()
            if t.ch_id == 0:
                dut.ch0_valid_i.value = 1
                dut.ch0_data_i.value = t.data[i];
                dut._log.info("%s driver0 drivered channle data %8x", time_ns, t.data[i])
                await FallingEdge(dut.clk_i)
                while dut.ch0_ready_o != 1:
                    await RisingEdge(dut.clk_i)
            elif t.ch_id == 1:
                dut.ch1_valid_i.value = 1
                dut.ch1_data_i.value = t.data[i];
                dut._log.info("%s driver1 drivered channle data %8x", time_ns, t.data[i])
                await FallingEdge(dut.clk_i)
                while dut.ch1_ready_o != 1:
                    await RisingEdge(dut.clk_i)
            elif t.ch_id == 2:
                dut.ch2_valid_i.value = 1
                dut.ch2_data_i.value = t.data[i];
                dut._log.info("%s driver2 drivered channle data %8x", time_ns, t.data[i])
                await FallingEdge(dut.clk_i)
                while dut.ch2_ready_o != 1:
                    await RisingEdge(dut.clk_i)

            for i in range(t.data_nidles):
                await self.chnl_idle(t)
        for i in range(t.pkt_nidles):
            await self.chnl_idle(t)

    async def chnl_idle(self, t):
        dut = self.dut
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
            
    async def mcdt_mon_bfm(self):
        dut = self.dut
        while True:
            m = mon_data_t()
            await RisingEdge(dut.clk_i)
            while(dut.inst_arbiter.data_val_o.value != 1):
                await RisingEdge(dut.clk_i)
            
            m.data = dut.inst_arbiter.arb_data_o.value
            m.data_id = dut.inst_arbiter.arb_id_o.value
            self.mcdt_mon_queue.put_nowait(m)
            time_ns = get_sim_time()
            dut._log.info("%s monitored mcdt data %8x and id %0d", time_ns, m.data, m.data_id)

    async def chnl_mon_bfm(self, ch_id):
        dut = self.dut
        while True:
            m = mon_data_t()
            await RisingEdge(dut.clk_i)
            if ch_id == 0:
                while str(dut.inst_slva_fifo_0.chx_valid_i.value) != '1' or str(
                        dut.inst_slva_fifo_0.chx_ready_o.value) != '1':
                    await RisingEdge(dut.clk_i)
                m.data = dut.inst_slva_fifo_0.chx_data_i.value
            elif ch_id == 1:
                while str(dut.inst_slva_fifo_1.chx_valid_i.value) != '1' or str(
                        dut.inst_slva_fifo_1.chx_ready_o.value) != '1':
                    await RisingEdge(dut.clk_i)
                m.data = dut.inst_slva_fifo_1.chx_data_i.value
            elif ch_id == 2:
                while str(dut.inst_slva_fifo_2.chx_valid_i.value) != '1' or str(
                        dut.inst_slva_fifo_2.chx_ready_o.value) != '1':
                    await RisingEdge(dut.clk_i)
                m.data = dut.inst_slva_fifo_2.chx_data_i.value
            self.chnl_mon_queue[ch_id].put(m)

            time_ns = get_sim_time()
            dut._log.info("%s monitored channle data %8x", time_ns, m.data)

    async def checker_bfm(self):
        dut = self.dut
        error_count = 0
        cmp_count = 0
        in_mbs = self.chnl_mon_queue
        out_mb = self.mcdt_mon_queue

        im = mon_data_t()
        om = mon_data_t()
        while True:
            while out_mb.empty():
                await RisingEdge(dut.clk_i)
            om = out_mb.get();
            if om.data_id == 0 or om.data_id == 1 or om.data_id == 2:
                while in_mbs[om.data_id].empty():
                    await RisingEdge(dut.clk_i)
                im = in_mbs[om.data_id].get();
            else: 
                dut._log.info("id %0d is not available", om.data_id)   
                    
            if om.data != im.data:
                error_count = error_count + 1;
                dut._log.info("[CMPFAIL] Compared failed! mcdt out data %8x ch_id %0d is not equal with channel in data %8x", om.data, om.data_id, im.data)
            else:
                dut._log.info("[CMPSUCD] Compared succeeded! mcdt out data %8x ch_id %0d is equal with channel in data %8x", om.data, om.data_id, im.data)

            cmp_count = cmp_count + 1;
    
    async def startup_bfms(self):
        # await self.reset()
        await cocotb.start(self.driver_bfm(0))
        await cocotb.start(self.driver_bfm(1))
        await cocotb.start(self.driver_bfm(2))

        await cocotb.start(self.chnl_mon_bfm(0))
        await cocotb.start(self.chnl_mon_bfm(1))
        await cocotb.start(self.chnl_mon_bfm(2))

        await cocotb.start(self.mcdt_mon_bfm())

        await cocotb.start(self.checker_bfm())
        
@cocotb.test()
async def test_mcdt(dut):
    await cocotb.start(generate_clock(dut))  # run the clock "in the background"
    await cocotb.start(generate_rst(dut))  # run the clock "in the background"
    
    bfm = McdtBfm(dut)
    await bfm.startup_bfms()
    
    await RisingEdge(dut.rstn_i)
    await bfm.send_trans(0)
    await bfm.send_trans(1)
    await bfm.send_trans(2)
    for i in range(50):
        await RisingEdge(dut.clk_i)
    
