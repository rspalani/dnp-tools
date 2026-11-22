# -*- coding: utf-8 -*-
"""
bu.py  -  DNP build-up (intensity against the build-up time D1) with a live plot,
from a settings file (TopSpin / Jython)

On TopSpin's command line:
    bu p1            run /opt/nmrdata/dnp_settings/bu_p1.py
    bu bu_p1         the same (the old name buildup_p1 also works)
    bu               choose the settings file from a list
New settings files are made by copying bu_template.py in
/opt/nmrdata/dnp_settings. The code is in /opt/dnptools/dnp_core.py, shared with
fs.py; its header describes the run, the timing, and the files written.
"""
import sys

DNP_CORE = "/opt/dnptools/dnp_core.py"

if __name__ == "__main__":
    execfile(DNP_CORE)
    run_buildup_settings(sys.argv[1:])
