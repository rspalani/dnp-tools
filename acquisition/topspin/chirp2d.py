# -*- coding: utf-8 -*-
"""
chirp2d.py  -  DNP enhancement over a grid of chirp widths and chirp times at one centre
frequency, with a live map, from a settings file (TopSpin / Jython)

On TopSpin's command line:
    chirp2d p1             run /opt/nmrdata/dnp_settings/chirp2d_p1.py
    chirp2d chirp2d_p1     the same
    chirp2d                choose the settings file from a list
New settings files are made by copying chirp2d_template.py in /opt/nmrdata/dnp_settings.
The code is in /opt/dnptools/dnp_core.py, shared with fs.py, bu.py, decay.py, and
powdep.py; its header describes the run, the timing, and the files written.
"""
import sys

DNP_CORE = "/opt/dnptools/dnp_core.py"

if __name__ == "__main__":
    execfile(DNP_CORE)
    run_chirp2d_settings(sys.argv[1:])
