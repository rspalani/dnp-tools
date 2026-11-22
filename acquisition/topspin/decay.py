# -*- coding: utf-8 -*-
"""
decay.py  -  decay of the DNP-enhanced polarization after the microwaves are switched
off, with a live plot, from a settings file (TopSpin / Jython)

On TopSpin's command line:
    decay p1           run /opt/nmrdata/dnp_settings/decay_p1.py
    decay decay_p1     the same
    decay              choose the settings file from a list
New settings files are made by copying decay_template.py in /opt/nmrdata/dnp_settings.
The code is in /opt/dnptools/dnp_core.py, shared with fs.py and bu.py; its header
describes the run, the timing, and the files written.
"""
import sys

DNP_CORE = "/opt/dnptools/dnp_core.py"

if __name__ == "__main__":
    execfile(DNP_CORE)
    run_decay_settings(sys.argv[1:])
