# -*- coding: utf-8 -*-
"""
fs.py  -  DNP frequency profile with a live plot, from a settings file
(TopSpin / Jython)

On TopSpin's command line:
    fs bdpa            run /opt/nmrdata/dnp_settings/fs_bdpa.py
    fs fs_bdpa         the same (the old name settings_bdpa also works)
    fs                 choose the settings file from a list
New settings files are made by copying fs_template.py in
/opt/nmrdata/dnp_settings. The code is in /opt/dnptools/dnp_core.py; its header
describes the run, the timing, and the files written.
"""
import sys

DNP_CORE = "/opt/dnptools/dnp_core.py"

if __name__ == "__main__":
    execfile(DNP_CORE)
    run_settings(sys.argv[1:])
