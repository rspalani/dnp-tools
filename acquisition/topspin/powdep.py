# -*- coding: utf-8 -*-
"""
powdep.py  -  DNP enhancement against mm-wave power at one frequency (the AWG drive
voltage changes from record to record), with a live plot, from a settings file
(TopSpin / Jython)

On TopSpin's command line:
    powdep p1           run /opt/nmrdata/dnp_settings/powdep_p1.py
    powdep powdep_p1    the same
    powdep              choose the settings file from a list
New settings files are made by copying powdep_template.py in /opt/nmrdata/dnp_settings.
The code is in /opt/dnptools/dnp_core.py, shared with fs.py, bu.py, and decay.py; its
header describes the run, the timing, and the files written. The source's power
calibration is /opt/dnptools/awg_power_cal.txt.
"""
import sys

DNP_CORE = "/opt/dnptools/dnp_core.py"

if __name__ == "__main__":
    execfile(DNP_CORE)
    run_powdep_settings(sys.argv[1:])
