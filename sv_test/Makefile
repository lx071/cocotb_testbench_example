#############################
# User variables
#############################
TB       = tb2
SEED     = 1

DFILES   += ../arbiter.v
DFILES   += ../slave_fifo.v
DFILES   += ../mcdt.v

VFILES  += $(TB).sv


#############################
# Environment variables
#############################
VCOMP                = iverilog -g2012 -o run.out
RUN                  = vvp -n run.out


comp:
	$(VCOMP) $(DFILES) $(VFILES)

run:
	$(RUN) 

clean:
	rm -rf AN.DB DVEfiles csrc *.simv *.simv.daidir *.simv.vdb ucli.key
	rm -rf *.log* *.vpd urgReport run.out

