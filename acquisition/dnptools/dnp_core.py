# -*- coding: utf-8 -*-
"""
dnp_core.py  -  shared acquisition code for the DNP frequency-profile, build-up,
and decay scripts (TopSpin / Jython)

Not run directly. The TopSpin script fs.py (in TopSpin's py/user folder) runs
    execfile("/opt/dnptools/dnp_core.py")
    run_settings(sys.argv[1:])
execfile is used instead of import so that TopSpin always runs the current
version of this file; an imported module can stay cached in TopSpin's Jython
until TopSpin is restarted.

Settings files: one per kind of experiment, in /opt/nmrdata/dnp_settings, named
<type>_<name>.py (fs_, bu_, decay_, powdep_, chirp2d_); a new one is made by copying
<type>_template.py there. The older names settings_<name>.py (fs) and buildup_<name>.py
(bu) are still found, with a note naming the new name; a file only in the old folder
/opt/nmrdata/fs_settings is not run (the message says what to copy where).
'fs bdpa' (or 'fs fs_bdpa') on TopSpin's command line uses
fs_bdpa.py; 'fs' alone lists the settings files to choose from, which is
also what happens if TopSpin does not pass the name on to the script. A
settings file is Python: plain assignments, run with frange() available. Its
UPPERCASE names are settings (list and defaults in SETTINGS below); an
UPPERCASE name that is not in the list stops the script, because it is
usually a typo. Lowercase names, such as frequency segments, are ignored.
RUN_LABEL defaults to <name>. The template itself is not run.

Dataset and template: DATA_DIR, DATA_NAME and TEMPLATE_EXPNO set in the
settings file are used. If DATA_DIR and DATA_NAME are both empty, the dataset open in TopSpin
when the script starts is used; if TEMPLATE_EXPNO is empty (None), the expno
open in TopSpin is the template, and it must belong to the run's dataset. The
confirmation dialog shows the dataset, the new expnos and the template in large
type, with where each came from. Before the dialog, and again after OK, the
script checks that none of the planned expnos exists yet; if some do, it stops
and names the first START_EXPNO with enough free expnos.

Run plan: REPEATS sets. Each set is an optional OFF reference, one ON record
per frequency in FREQS, and an optional final OFF reference, selected with
OFF_MODE. Every set occupies a fixed block of expnos from START_EXPNO on; a
point that cannot be set on the AWG is skipped and its expno is left empty.

Records: each run gets a folder inside the dataset,
    <DATA_DIR>/<DATA_NAME>/dnp_runs/<RUN_LABEL>_<type>_<YYYYMMDD-HHMMSS>_e<START_EXPNO>/
named after the label, the type (fs, bu, decay, powdep, chirp2d) and the time the
run started, e.g. p1_bu_20261122-210455_e600. Runs from before November 2026 are in
<dataset>/fs_runs/<YYYYMMDD-HHMMSS>_<RUN_LABEL>_e<START_EXPNO>/; the viewer reads both. It holds run.txt (one line per finished
record, read by dnp_viewer.py and fs_rephase.py), log.txt (every step,
time-stamped), a copy of the settings file, settings.txt (every setting as
used, including the full frequency list), and the viewer's files (viewer.log, plot.png, values.tsv,
phase.txt). Because the folder is inside the dataset, it is copied with it.
One line is also appended to the common index /opt/nmrdata/dnp_runs.tsv when a
run starts and one when it ends; its last column is the type. (The index of the
older runs is /opt/nmrdata/fs_runs.tsv, which is no longer written.)

Live plot: the viewer dnp_viewer.py (system Python 3) is started in the
background. It reads run.txt and the processed spectra (pdata/1/1r, 1i) and
plots the intensity per scan, or I_on/I_off - 1 when start OFFs are recorded,
against frequency, one series per set. Closing the viewer does not affect the
run; it can be reopened at any time with the command printed in the log, e.g.
    python3 /opt/dnptools/dnp_viewer.py <run folder>/run.txt
With RESPAWN_VIEWER = True, each time a record is added to run.txt, pgrep is
used to check whether a viewer for this run is running, and one is started if
not; a viewer closed during a record reappears once that record has been
added. A viewer opened by hand with the command above counts as running.

XCMD("zg", wait=WAIT_TILL_DONE) returns before the acquisition has finished on
this spectrometer, so each record is timed here:
  1. After zg the script sleeps until (NS+DS)*D1 has elapsed; the acquisition
     cannot finish earlier than that.
  2. It then checks the expno every POLL_INTERVAL s until audita.txt has been
     written after that point (TopSpin writes it when the acquisition ends).
  3. It processes the record with PROCESS_CMDS (default: efp, absn), waits
     POST_ACQ_PAD s, and only then sends the next AWG command.
Polling continues up to a deadline of
    (NS+DS)*(D1+SCAN_OVERHEAD) + MAX_EXTRA_WAIT   s after zg,
where the first term is the expected duration of the record. The record is
accepted whenever audita.txt appears before the deadline, including after
the expected duration. Only if it has not appeared by the deadline does the
script send 'stop' to the AWG, show an error box, and end without starting
further records.

If the script is stopped from TopSpin, mm-wave 'stop' is sent and run.txt
ends with '# end: stopped: interrupted ...'.
Build-up runs (TopSpin script bu.py): 'bu p1' runs bu_p1.py from the same
folder, 'bu' alone lists the bu_*.py files, and bu_template.py is the
template. A build-up run acquires one record per build-up time D1, either at
one mm-wave frequency (FREQ and POWER; 'cw' is sent to the AWG before each ON
record) or with the microwaves off ('stop' before each OFF record). The pulse
program must saturate before D1, so that every scan starts from zero
polarization. The settings that differ from a profile:
    D1_LIST      build-up times (s), acquired in the order written; logspace(first,
                 last, n) gives n log-spaced values
    NS_LIST      scans per ON record: one number, or one per D1; ns_for_time(D1_LIST,
                 seconds, ...) gives more scans at short delays
    OFF_NS_LIST  the same for the OFF records (None: NS_LIST)
    SERIES       the records of each set: "on" or "off" (one record per D1),
                 "interleaved" (ON and OFF at each D1, back to back), "on_then_off"
                 or "off_then_on" (all of one kind, then all of the other)
    FREQ, POWER  the ON records' 'cw' command (not needed for SERIES "off")
    FREQS        instead of FREQ (SERIES "on" only): one build-up per entry, a frequency
                 (GHz, with POWER) or a (frequency, power) pair; each is its own set
                 (with REPEATS, the repeats follow as further sets), and run.txt lists
                 them ('# set_cw = <set> <GHz> <power>; ...')
    FREQ_ORDER   with FREQS: "by_d1" (at each D1, every frequency in turn; default) or
                 "by_freq" (one whole build-up after the other); expnos in acquisition order
Template, expno checks, timing, run folder, index and viewer are as for a
profile. The run folder is in dnp_runs as well, <name>_bu_<time>_e<expno> unless
RUN_LABEL is set; run.txt has '# type = buildup' and an eighth column with D1
(s), and settings.txt lists every planned record with its expected duration.

Decay runs (TopSpin script decay.py): 'decay p1' runs decay_p1.py, 'decay' alone
lists the decay_*.py files, and decay_template.py is the template. Each set
(REPEATS) sends 'cw FREQ POWER', waits so that the reference pulse comes
POLARIZE_TIME s after 'cw', acquires the reference record with the microwaves on,
sends 'stop' (t = 0), and then acquires one record at each target time in
TIMES_LIST. Every record has NS 1 and DS 0; the pulse program must not saturate,
and its pulse should be a small flip angle (FLIP_DEG, written to run.txt for the
viewer, which corrects for the polarization each pulse uses). The D1 of a decay
record is set when the record is set up:
    D1 = target - (now - t_off) - latency
where latency, the time from setting D1 to the pulse besides D1, is the median of
those measured on the records so far (pulse time = end of acquisition, the mtime
of audita.txt, less AQ = TD/(2*SW_h)), ZG_LATENCY before the first measurement.
A D1 below MIN_D1 is raised to it, so the record comes late; this is logged, and
the time actually reached is recorded. run.txt has '# type = decay', the flip
angle, and three more columns: D1 (s), t (s after 'stop'; negative for the
reference), and the target time.

Power-dependence runs (TopSpin script powdep.py): 'powdep p1' runs powdep_p1.py,
'powdep' alone lists the powdep_*.py files, and powdep_template.py is the
template. A power-dependence run is a profile at one frequency in which the AWG
drive voltage (the second argument of 'cw') changes from record to record: per
set an optional OFF record, one ON record per voltage, and an optional OFF
record, as OFF_MODE does for a profile. The voltages are given either directly
(VOLTAGES, in V) or as fractions of the power at full drive (POWER_FRACTIONS),
which are converted to voltages with the source's calibration,
/opt/dnptools/awg_power_cal.txt (drive voltage in mV against output power in mW,
measured at one frequency; the ratio P(V)/P(full drive) is taken to hold at every
frequency). Full drive is MAX_AWG_VOLTAGE (0.4 V); no script sends a larger
voltage, and fs, bu, and decay refuse a POWER above it. Voltages below the lowest
calibration point are refused, since their power is not known. run.txt has
'# type = powdep', the calibration used, and an eighth column with the drive
voltage (V).

Chirp grids (TopSpin script chirp2d.py): 'chirp2d p1' runs chirp2d_p1.py, 'chirp2d'
alone lists the chirp2d_*.py files, and chirp2d_template.py is the template. Per set:
an optional OFF, one CW record at FREQ (CW_RECORD), one ON record per chirp of the
grid WIDTHS_MHZ x TIMES_US, and an optional OFF. A chirp record is sent
'chirp FREQ <width MHz> <time us> <shape> POWER' (shape I, D, V or IV, as the AWG
server reads it), the CW record 'cw FREQ POWER'. RATE_RANGE keeps only the chirps
whose sweep rate (width/time, twice that for V and IV) lies in it, and ORDER
'center_out' acquires them from the rate closest to RATE_CENTER outwards (so a run
cut short has the chirps of most interest), 'grid' row by row. run.txt has
'# type = chirp2d', the grid, the chirps in acquisition order ('# chirps'), and two
more columns, width (MHz) and time (us).

OFF reference from another run (fs, powdep, chirp2d): OFF_REF = an expno of this
dataset, or the path of an expno folder in another, uses that OFF record as the
reference for I_on/I_off instead of the start OFF of each set (OFF records that the
run acquires itself, OFF_MODE, then only check the drift). Before the run, its
processed spectrum is checked for, and its RG, pulse length, power, and pulse
program (from its acqus, the parameters it was acquired with) are compared with the
template's current ones (its acqu, which the new records get), and its D1 with the
run's; a difference is shown as a warning in the confirmation dialog. run.txt has '# off_ref = <expno folder>'.
"""
import math
import os
import re
import time
import subprocess

# TopSpin's Jython environment rebinds the name Exception (an IOError went
# straight through such a handler in TopSpin 3.6.2), so the handlers here use
# CATCH: Python's own base class, taken from the builtins module, plus
# java.lang.Exception for errors raised on TopSpin's Java side. Stopping the
# script from TopSpin raises java.lang.ThreadDeath, an Error, which is
# deliberately not caught.
try:
    import __builtin__ as _builtins
except ImportError:
    import builtins as _builtins
try:
    from java.lang import Exception as _JavaException
    CATCH = (_builtins.Exception, _JavaException)
except ImportError:
    CATCH = (_builtins.Exception,)


class RunAbort(_builtins.Exception):
    pass


# ---- Installation -----------------------------------------------------------
DNPTOOLS      = "/opt/dnptools"
AWG_PYTHON    = "python"                        # interpreter that runs awg_cmd.py
AWG_CMD_PATH  = DNPTOOLS + "/awg_cmd.py"
VIEWER_PYTHON = "/usr/bin/python3"
VIEWER_PATH   = DNPTOOLS + "/dnp_viewer.py"
INDEX_PATH    = "/opt/nmrdata/dnp_runs.tsv"      # common index, one line per run start and end
RUNS_SUBDIR   = "dnp_runs"                       # run folders, inside each dataset
SETTINGS_DIR  = "/opt/nmrdata/dnp_settings"      # <type>_<name>.py files
OLD_SETTINGS_DIR = "/opt/nmrdata/fs_settings"   # before November 2026; checked, never run
POWER_CAL_PATH  = DNPTOOLS + "/awg_power_cal.txt"   # drive voltage (mV) -> source power (mW)
VERSION_PATH    = DNPTOOLS + "/VERSION"         # written by deploy/update.sh: the deployed commit
MAX_AWG_VOLTAGE = 0.4                           # full drive: the largest second argument of 'cw'



def code_version():
    """The deployed code version: the first line of VERSION_PATH, written by
    deploy/update.sh (commit, its date, and when it was installed). Copied into
    every run.txt as '# code_version', so a run can be traced to its code."""
    try:
        fh = open(VERSION_PATH)
        try:
            line = fh.readline().strip()
        finally:
            fh.close()
        return line.replace("\t", " ") or "unknown (VERSION is empty)"
    except CATCH:
        return "unknown (no %s)" % VERSION_PATH

# ---- Settings: (name, default) ------------------------------------------------
REQUIRED = "<required>"
SETTINGS = [
    ("RUN_LABEL",        REQUIRED),   # short name in the run id; default: <name> of fs_<name>.py
    ("SAMPLE",           ""),
    ("MAS_INFO",         ""),
    ("DATA_DIR",         ""),         # "" (with DATA_NAME "") = the dataset open in TopSpin
    ("DATA_NAME",        ""),
    ("POWER",            REQUIRED),
    ("START_EXPNO",      REQUIRED),
    ("TEMPLATE_EXPNO",   None),       # None = the expno open in TopSpin
    ("REPEATS",          1),
    ("OFF_MODE",         "both"),     # "start", "end", "both" or "none"
    ("OFF_REF",          None),       # expno (or expno folder) of an earlier OFF record
    ("FREQS",            REQUIRED),   # list of frequencies (GHz), in acquisition order
    ("D1",               REQUIRED),
    ("DS",               0),
    ("PROFILE_NS",       REQUIRED),
    ("OFF_SCANS",        REQUIRED),
    ("AWG_SETTLE",       2),
    ("SCAN_OVERHEAD",    5),
    ("POLL_INTERVAL",    5),
    ("MAX_EXTRA_WAIT",   300),
    ("POST_ACQ_PAD",     5),
    ("EST_OVERHEAD",     5),
    ("AWG_RETRIES",      3),
    ("MAX_CONSEC_SKIPS", 3),
    ("PROCESS_CMDS",     ["efp", "absn"]),
    ("PEAK_PPM",         None),       # None = whole spectrum
    ("PEAK_WINDOW_PPM",  10.0),
    ("INTENSITY_MODE",   "extreme"),  # "extreme", "max" or "sum"
    ("LAUNCH_VIEWER",    True),
    ("RESPAWN_VIEWER",   True),
]

# Build-up runs (bu.py): the settings that differ from a profile are SERIES, FREQ,
# D1_LIST, NS_LIST and OFF_NS_LIST; POWER is needed only with ON records
BU_SERIES = ("on", "off", "interleaved", "on_then_off", "off_then_on")
BU_SETTINGS = [
    ("RUN_LABEL",        REQUIRED),   # short name in the run id; default: bu_<name> of bu_<name>.py
    ("SAMPLE",           ""),
    ("MAS_INFO",         ""),
    ("DATA_DIR",         ""),         # "" (with DATA_NAME "") = the dataset open in TopSpin
    ("DATA_NAME",        ""),
    ("START_EXPNO",      REQUIRED),
    ("TEMPLATE_EXPNO",   None),       # None = the expno open in TopSpin
    ("REPEATS",          1),
    ("SERIES",           "on"),       # one of BU_SERIES
    ("FREQ",             None),       # GHz, for the ON records (not needed for SERIES "off")
    ("FREQS",            None),       # instead of FREQ: several frequencies (GHz), or (GHz, power)
                                      # pairs, one build-up each (SERIES "on" only)
    ("FREQ_ORDER",       "by_d1"),    # with FREQS: "by_d1" (at each D1, every frequency in turn)
                                      # or "by_freq" (the whole build-up of one frequency, then the next)
    ("POWER",            None),       # second argument of 'cw' (not needed for SERIES "off")
    ("D1_LIST",          REQUIRED),   # build-up times (s), in acquisition order
    ("NS_LIST",          REQUIRED),   # scans per ON record: one number, or a list with one per D1
    ("OFF_NS_LIST",      None),       # scans per OFF record, as NS_LIST; None = NS_LIST
    ("DS",               0),
    ("AWG_SETTLE",       2),
    ("SCAN_OVERHEAD",    5),
    ("POLL_INTERVAL",    5),
    ("MAX_EXTRA_WAIT",   300),
    ("POST_ACQ_PAD",     5),
    ("EST_OVERHEAD",     5),
    ("AWG_RETRIES",      3),
    ("MAX_CONSEC_SKIPS", 3),
    ("PROCESS_CMDS",     ["efp", "absn"]),
    ("PEAK_PPM",         None),       # None = whole spectrum
    ("PEAK_WINDOW_PPM",  10.0),
    ("INTENSITY_MODE",   "extreme"),  # "extreme", "max" or "sum"
    ("LAUNCH_VIEWER",    True),
    ("RESPAWN_VIEWER",   True),
]


# Decay runs (decay.py): polarize with the microwaves on, one reference record, microwaves
# off, then one record (NS 1) at each target time after the microwaves went off
DECAY_SETTINGS = [
    ("RUN_LABEL",        REQUIRED),   # default: decay_<name> of decay_<name>.py
    ("SAMPLE",           ""),
    ("MAS_INFO",         ""),
    ("DATA_DIR",         ""),
    ("DATA_NAME",        ""),
    ("START_EXPNO",      REQUIRED),
    ("TEMPLATE_EXPNO",   None),
    ("REPEATS",          1),          # polarize-and-decay cycles, one after the other
    ("FREQ",             REQUIRED),   # GHz, while polarizing
    ("POWER",            REQUIRED),   # second argument of 'cw'
    ("POLARIZE_TIME",    REQUIRED),   # s from 'cw' to the reference pulse
    ("TIMES_LIST",       REQUIRED),   # s after the microwaves go off, increasing: one record each
    ("FLIP_DEG",         5.0),        # flip angle of the template's pulse (for the viewer's correction)
    ("ZG_LATENCY",       3.0),        # s from setting D1 to the pulse, besides D1 (first guess;
                                      # then measured on each record)
    ("MIN_D1",           0.5),        # s; a target that comes sooner is taken late, with this D1
    ("AWG_SETTLE",       2),
    ("SCAN_OVERHEAD",    5),
    ("POLL_INTERVAL",    1),
    ("MAX_EXTRA_WAIT",   300),
    ("POST_ACQ_PAD",     0),
    ("EST_OVERHEAD",     5),
    ("AWG_RETRIES",      3),
    ("PROCESS_CMDS",     ["efp", "absn"]),
    ("PEAK_PPM",         None),
    ("PEAK_WINDOW_PPM",  10.0),
    ("INTENSITY_MODE",   "extreme"),
    ("LAUNCH_VIEWER",    True),
    ("RESPAWN_VIEWER",   True),
]


# Power-dependence runs (powdep.py): a profile at one frequency over AWG drive voltages
POWDEP_SETTINGS = [
    ("RUN_LABEL",        REQUIRED),   # default: powdep_<name> of powdep_<name>.py
    ("SAMPLE",           ""),
    ("MAS_INFO",         ""),
    ("DATA_DIR",         ""),
    ("DATA_NAME",        ""),
    ("START_EXPNO",      REQUIRED),
    ("TEMPLATE_EXPNO",   None),
    ("REPEATS",          1),
    ("OFF_MODE",         "both"),     # "start", "end", "both" or "none"
    ("OFF_REF",          None),       # expno (or expno folder) of an earlier OFF record
    ("FREQ",             REQUIRED),   # GHz, for every ON record
    ("VOLTAGES",         None),       # AWG drive voltages (V), in acquisition order; or
    ("POWER_FRACTIONS",  None),       # fractions of the power at full drive, in acquisition order
    ("POWER_CAL",        None),       # calibration file; None = POWER_CAL_PATH
    ("D1",               REQUIRED),
    ("DS",               0),
    ("ON_SCANS",         REQUIRED),
    ("OFF_SCANS",        REQUIRED),
    ("AWG_SETTLE",       2),
    ("SCAN_OVERHEAD",    5),
    ("POLL_INTERVAL",    5),
    ("MAX_EXTRA_WAIT",   300),
    ("POST_ACQ_PAD",     5),
    ("EST_OVERHEAD",     5),
    ("AWG_RETRIES",      3),
    ("MAX_CONSEC_SKIPS", 3),
    ("PROCESS_CMDS",     ["efp", "absn"]),
    ("PEAK_PPM",         None),
    ("PEAK_WINDOW_PPM",  10.0),
    ("INTENSITY_MODE",   "extreme"),
    ("LAUNCH_VIEWER",    True),
    ("RESPAWN_VIEWER",   True),
]


# Chirp grids (chirp2d.py): chirp width x chirp time at one centre frequency
CHIRP2D_SETTINGS = [
    ("RUN_LABEL",        REQUIRED),   # default: chirp2d_<name> of chirp2d_<name>.py
    ("SAMPLE",           ""),
    ("MAS_INFO",         ""),
    ("DATA_DIR",         ""),
    ("DATA_NAME",        ""),
    ("START_EXPNO",      REQUIRED),
    ("TEMPLATE_EXPNO",   None),
    ("REPEATS",          1),
    ("OFF_MODE",         "none"),     # "start", "end", "both" or "none"
    ("OFF_REF",          None),       # expno (or expno folder) of an earlier OFF record
    ("FREQ",             REQUIRED),   # GHz, centre of every chirp and the CW frequency
    ("POWER",            0.4),        # AWG drive voltage (V) for the chirps and the CW record
    ("WIDTHS_MHZ",       REQUIRED),   # chirp widths (MHz, at the output), each > 0
    ("TIMES_US",         REQUIRED),   # chirp times (us), each > 0
    ("CHIRP_SHAPE",      "I"),        # I increasing, D decreasing, V, IV inverted V
    ("RATE_RANGE",       None),       # (lo, hi) MHz/us: only the chirps with a rate in it
    ("ORDER",            "center_out"),   # "center_out" (from RATE_CENTER) or "grid"
    ("RATE_CENTER",      10.0),       # MHz/us
    ("CW_RECORD",        True),       # one CW record per set, before the chirps
    ("D1",               REQUIRED),
    ("DS",               0),
    ("ON_SCANS",         1),
    ("OFF_SCANS",        1),
    ("AWG_SETTLE",       5),
    ("SCAN_OVERHEAD",    5),
    ("POLL_INTERVAL",    5),
    ("MAX_EXTRA_WAIT",   300),
    ("POST_ACQ_PAD",     5),
    ("EST_OVERHEAD",     5),
    ("AWG_RETRIES",      3),
    ("MAX_CONSEC_SKIPS", 3),
    ("PROCESS_CMDS",     ["efp", "absn"]),
    ("PEAK_PPM",         None),
    ("PEAK_WINDOW_PPM",  10.0),
    ("INTENSITY_MODE",   "extreme"),
    ("LAUNCH_VIEWER",    True),
    ("RESPAWN_VIEWER",   True),
]
CHIRP_SHAPES = {"I": "increasing", "D": "decreasing", "V": "V-shaped", "IV": "inverted V"}


def chirp_rate(width, t, shape):
    """Sweep rate (MHz/us) of a chirp: width/time, twice that for V and IV (the span is
    swept twice per chirp)."""
    return (2.0 if shape in ("V", "IV") else 1.0) * width / t


def frange(start, stop, step):
    result = []
    current = start
    while current <= stop + (step / 2.0):
        result.append(current)
        current += step
    return result



def logspace(first, last, n, digits=3):
    """n values from first to last (both as given), evenly spaced on a logarithmic scale,
    the ones in between rounded to `digits` significant digits; e.g. build-up times."""
    n = int(n)
    if float(first) <= 0 or float(last) <= 0 or n < 1:
        raise ValueError("logspace(first, last, n) needs first > 0, last > 0 and n >= 1")
    if n == 1:
        return [first]
    out = [first]
    ratio = float(last) / float(first)
    for i in range(1, n - 1):
        v = float(first) * ratio ** (float(i) / (n - 1))
        v = round(v, digits - 1 - int(math.floor(math.log10(v))))
        out.append(int(v) if v == int(v) else v)
    out.append(last)
    return out


def ns_for_time(d1_list, seconds, ns_min=None, ns_max=None, multiple=1, overhead=0.0):
    """Scans per record for records of about `seconds` each: seconds / (D1 + overhead)
    for each D1 in d1_list, at most ns_max, rounded down to a multiple of `multiple`
    (e.g. the phase cycle), and at least ns_min (default: multiple). overhead: s per
    scan besides D1 (e.g. SCAN_OVERHEAD)."""
    multiple = max(1, int(multiple))
    lo = multiple if ns_min is None else int(ns_min)
    out = []
    for d1 in d1_list:
        ns = int(float(seconds) / (float(d1) + float(overhead)))
        if ns_max is not None:
            ns = min(ns, int(ns_max))
        out.append(max(lo, (ns // multiple) * multiple))
    return out


def read_power_cal(path):
    """(freq_GHz or None, [V], [mW]) from a calibration file: one 'mV mW' pair per line,
    and optionally a line 'freq_GHz = <GHz>'; '#' starts a comment. Raises ValueError if
    there are fewer than two points or the power does not rise with the voltage."""
    freq, pts = None, []
    fh = open(path)
    try:
        for line in fh:
            body = line.split("#", 1)[0].strip()
            if not body:
                continue
            m = re.match(r"freq_GHz\s*=\s*(\S+)$", body)
            if m:
                freq = float(m.group(1))
                continue
            parts = body.replace(",", " ").split()
            if len(parts) != 2:
                raise ValueError("line '%s' is not 'mV mW'" % body)
            pts.append((float(parts[0]) / 1000.0, float(parts[1])))
    finally:
        fh.close()
    pts.sort()
    if len(pts) < 2:
        raise ValueError("fewer than two points")
    vs, ps = [p[0] for p in pts], [p[1] for p in pts]
    for i in range(1, len(pts)):
        if not (vs[i] > vs[i - 1] and ps[i] > ps[i - 1]):
            raise ValueError("the power must rise with the voltage (at %g mV)" % (vs[i] * 1000.0))
    return freq, vs, ps


def mono_slopes(xs, ys):
    """Slopes at the points for a monotone piecewise-cubic (Fritsch-Carlson, as PCHIP)
    interpolation of increasing data; dnp_viewer.py uses the same."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    if n == 2:
        return [d[0], d[0]]
    m = [d[0]] + [0.0] * (n - 2) + [d[-1]]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    return m


def mono_interp(xs, ys, m, x):
    """The interpolant through (xs, ys) with slopes m at x (xs[0] <= x <= xs[-1])."""
    i = 0
    while i < len(xs) - 2 and x > xs[i + 1]:
        i += 1
    h = xs[i + 1] - xs[i]
    t = (x - xs[i]) / h
    return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i] + (t ** 3 - 2 * t ** 2 + t) * h * m[i]
            + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1] + (t ** 3 - t ** 2) * h * m[i + 1])


def power_of_voltage(cal, v):
    """Source power (mW, at the calibration frequency) at drive voltage v (V)."""
    return mono_interp(cal["v"], cal["p"], cal["m"], v)


def voltage_of_fraction(cal, f):
    """Drive voltage (V) whose power is the fraction f of the power at full drive."""
    target = f * cal["p_full"]
    lo, hi = cal["v"][0], MAX_AWG_VOLTAGE
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if power_of_voltage(cal, mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def load_power_cal(path):
    """The calibration as a dict (freq, v, p, m, p_full, path); raises ValueError."""
    freq, vs, ps = read_power_cal(path)
    if vs[-1] < MAX_AWG_VOLTAGE - 1e-9:
        raise ValueError("it ends at %g mV, below full drive (%g mV)" % (vs[-1] * 1000.0, MAX_AWG_VOLTAGE * 1000.0))
    cal = {"freq": freq, "v": vs, "p": ps, "m": mono_slopes(vs, ps), "path": path}
    cal["p_full"] = power_of_voltage(cal, MAX_AWG_VOLTAGE)
    return cal


def check_power(fail, name, v):
    """True if v (a number) is a usable second argument of 'cw': 0 < v <= MAX_AWG_VOLTAGE."""
    if not 0 < v <= MAX_AWG_VOLTAGE + 1e-9:
        fail("%s must be above 0 and at most %g, the largest AWG drive voltage (got %s)."
             % (name, MAX_AWG_VOLTAGE, v))
        return False
    return True


def kind_hint(S, cmd):
    """For an error box: the command the settings S look written for, if not cmd."""
    for name, keys, what in (("chirp2d", ("WIDTHS_MHZ", "TIMES_US", "CHIRP_SHAPE"), "chirp-grid"),
                             ("powdep", ("VOLTAGES", "POWER_FRACTIONS"), "power-dependence"),
                             ("decay", ("TIMES_LIST", "POLARIZE_TIME"), "decay"),
                             ("bu", ("D1_LIST", "SERIES", "NS_LIST"), "build-up"),
                             ("fs", ("FREQS", "PROFILE_NS"), "frequency-profile")):
        if name != cmd and [k for k in keys if k in S]:
            return "This looks like a %s settings file: run it with '%s'" % (what, name)
    return ""


def fmt_dur(sec):
    sec = int(round(sec))
    if sec >= 3600:
        return "%d h %02d min" % (sec // 3600, (sec % 3600) // 60)
    if sec >= 60:
        return "%d min %02d s" % (sec // 60, sec % 60)
    return "%d s" % sec


def html_text(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# The settings file prefix of each command is "<command>_"; fs and bu files had other
# prefixes before November 2026, which are still found (with a note naming the new name).
LEGACY_PREFIX = {"fs": "settings_", "bu": "buildup_"}
SETTINGS_NOTES = []      # notes for the confirmation dialog, set by run_from_args


def settings_prefixes(cmd):
    """[new prefix] or [new prefix, old prefix] of the settings files of command cmd."""
    return [cmd + "_"] + ([LEGACY_PREFIX[cmd]] if cmd in LEGACY_PREFIX else [])


def settings_files(cmd="fs", folder=None):
    """Names of the settings files of command cmd in folder (SETTINGS_DIR), templates left out."""
    folder = folder or SETTINGS_DIR
    try:
        names = os.listdir(folder)
    except CATCH:
        return []
    out = []
    for n in names:
        for p in settings_prefixes(cmd):
            if n.startswith(p) and n.endswith(".py") and n != p + "template.py":
                out.append(n)
                break
    return sorted(out)


def short_name(cmd, base):
    """'p1' for fs_p1.py, settings_p1.py, bu_p1.py, buildup_p1.py, ..."""
    stem = base[:-3] if base.endswith(".py") else base
    for p in settings_prefixes(cmd):
        if stem.startswith(p):
            return stem[len(p):]
    return stem


def choose_settings(cmd="fs"):
    """Lets the user pick a settings file; returns its name or None."""
    names = settings_files(cmd)
    if not names:
        ERRMSG("%s: there are no settings files in %s.\nCopy %s_template.py there to "
               "%s_<name>.py and fill it in." % (cmd, SETTINGS_DIR, cmd, cmd))
        return None
    from javax.swing import JOptionPane
    try:
        from jarray import array
        from java.lang import Object
        options = array(names, Object)
    except CATCH:
        options = names
    choice = JOptionPane.showInputDialog(
        None, "Settings file to run (in %s):" % SETTINGS_DIR, "%s: choose the settings" % cmd,
        JOptionPane.QUESTION_MESSAGE, None, options, options[0])
    if choice is None:
        return None
    return str(choice)


def settings_candidates(name, cmd):
    """File names that name ('p1', 'fs_p1', 'settings_p1', with or without .py) can mean,
    new names first."""
    stem = name[:-3] if name.endswith(".py") else name
    short = short_name(cmd, stem)
    out = []
    for c in [stem + ".py"] + [p + short + ".py" for p in settings_prefixes(cmd)]:
        if c not in out:
            out.append(c)
    return out


def settings_path(name, cmd="fs"):
    """(path, error) of the settings file meant by name: a path, '<cmd>_p1(.py)', 'p1', or an
    old name such as 'settings_p1'. Adds a note to SETTINGS_NOTES when an old name is used.
    error is '' or why nothing may be run: the file is not found, it is only in the old
    folder, or the old folder's copy was edited after it was copied to the new folder."""
    name = str(name).strip()
    if os.sep in name:
        p = name if name.endswith(".py") else name + ".py"
        return p, ("" if os.path.isfile(p) else "settings file %s not found" % p)
    new_base = cmd + "_" + short_name(cmd, name) + ".py"
    path = None
    for cand in settings_candidates(name, cmd):
        if os.path.isfile(os.path.join(SETTINGS_DIR, cand)):
            path = os.path.join(SETTINGS_DIR, cand)
            break
    if path is None:
        for cand in settings_candidates(name, cmd):
            old = os.path.join(OLD_SETTINGS_DIR, cand)
            if os.path.isfile(old):
                return old, ("%s is only in the old folder %s, which is no longer used.\n"
                             "Copy it to the new folder under its new name:\n"
                             "    cp -p %s %s\nthen run '%s %s' again."
                             % (cand, OLD_SETTINGS_DIR, old, os.path.join(SETTINGS_DIR, new_base),
                                cmd, short_name(cmd, cand)))
        avail = ", ".join([short_name(cmd, n) for n in settings_files(cmd)]) or "none"
        return os.path.join(SETTINGS_DIR, new_base), ("settings file %s not found.\nAvailable in %s: %s"
                                                      % (os.path.join(SETTINGS_DIR, new_base), SETTINGS_DIR, avail))
    base = os.path.basename(path)
    if base != new_base:
        SETTINGS_NOTES.append("%s has an old name; rename it to %s (the run is not affected)."
                              % (path, new_base))
    elif name not in (short_name(cmd, name), new_base, new_base[:-3]):
        SETTINGS_NOTES.append("'%s %s' is now '%s %s'." % (cmd, name, cmd, short_name(cmd, name)))
    # A copy in the old folder that is newer than this file was probably edited by habit.
    try:
        mine = os.path.getmtime(path)
        for cand in settings_candidates(base, cmd):
            old = os.path.join(OLD_SETTINGS_DIR, cand)
            if os.path.isfile(old) and os.path.getmtime(old) > mine + 1:
                return path, ("%s in the old folder was changed after it was copied to\n%s.\n"
                              "Only %s is used now. Make the change there (or copy the old file over it:\n"
                              "    cp -p %s %s)\nand run '%s %s' again."
                              % (old, path, SETTINGS_DIR, old, path, cmd, short_name(cmd, base)))
    except CATCH:
        pass
    return path, ""


def run_settings(args=None):
    """Entry point of fs.py. args: the words after 'fs' on TopSpin's command line."""
    run_from_args(args, "fs", run_profile)


def run_buildup_settings(args=None):
    """Entry point of bu.py. args: the words after 'bu' on TopSpin's command line."""
    run_from_args(args, "bu", run_buildup)


def run_decay_settings(args=None):
    """Entry point of decay.py. args: the words after 'decay' on TopSpin's command line."""
    run_from_args(args, "decay", run_decay)


def run_powdep_settings(args=None):
    """Entry point of powdep.py. args: the words after 'powdep' on TopSpin's command line."""
    run_from_args(args, "powdep", run_powdep)


def run_chirp2d_settings(args=None):
    """Entry point of chirp2d.py. args: the words after 'chirp2d' on TopSpin's command line."""
    run_from_args(args, "chirp2d", run_chirp2d)


def run_from_args(args, cmd, runner):
    """Finds and reads the settings file named in args (or chosen from a list) and runs it
    with runner. RUN_LABEL defaults to <name> of <cmd>_<name>.py; a RUN_LABEL that starts
    with '<cmd>_' loses that prefix, since the type is in the run folder name anyway."""
    del SETTINGS_NOTES[:]
    args = [str(a) for a in (args or []) if str(a).strip()]
    name = args[0] if args else choose_settings(cmd)
    if not name:
        MSG("%s: no settings file chosen; nothing was started." % cmd)
        return
    path, err = settings_path(name, cmd)
    base = os.path.basename(path)
    if base in [p + "template.py" for p in settings_prefixes(cmd)]:
        ERRMSG("%s: %s is the template and is not run.\nCopy it to "
               "%s/%s_<name>.py, fill it in, and run '%s <name>'." % (cmd, base, SETTINGS_DIR, cmd, cmd))
        return
    if err:
        ERRMSG("%s: %s\nNothing was started." % (cmd, err))
        return
    ns = {"frange": frange, "logspace": logspace, "ns_for_time": ns_for_time}
    try:
        execfile(path, ns)
    except CATCH as ex:
        ERRMSG("%s: error in the settings file %s:\n%s\nNothing was started." % (cmd, path, ex))
        return
    S = dict([(k, v) for k, v in ns.items() if k.isupper()])
    label = str(S.get("RUN_LABEL") or "").strip() or short_name(cmd, base)
    if label.startswith(cmd + "_") and len(label) > len(cmd) + 1:
        label = label[len(cmd) + 1:]
    S["RUN_LABEL"] = label
    runner(S, path)


def check_settings(S, table, hint=""):
    """All settings of table, with the defaults for those not in S; None (after an error
    box) if S has an unknown setting or lacks a required one. hint: added to the box
    when there are unknown settings."""
    names = [n for n, d in table]
    unknown = sorted([k for k in S.keys() if k.isupper() and k not in names])
    missing = [n for n, d in table
               if d == REQUIRED and (n not in S or S[n] is None or S[n] == "")]
    if unknown or missing:
        lines = []
        if unknown:
            lines.append("Unknown setting(s): %s" % ", ".join(unknown))
        if missing:
            lines.append("Missing setting(s): %s" % ", ".join(missing))
        if unknown and hint:
            lines.append(hint)
        ERRMSG("dnp_core.py: %s.\nNothing was started." % ".\n".join(lines))
        return None
    c = {}
    for n, d in table:
        if n in S:
            c[n] = S[n]
        elif isinstance(d, list):
            c[n] = list(d)
        else:
            c[n] = d
    return c


def failer(label):
    def fail(msg):
        ERRMSG("dnp_core.py (%s): %s\nNothing was started." % (label, msg))
    return fail


def run_profile(S, source=None):
    """Runs the profile described by the settings dict S; source: the settings file, if any."""
    # ---- Settings ------------------------------------------------------------
    c = check_settings(S, SETTINGS, kind_hint(S, "fs"))
    if c is None:
        return
    RUN_LABEL        = str(c["RUN_LABEL"]).strip()
    SAMPLE           = c["SAMPLE"]
    MAS_INFO         = c["MAS_INFO"]
    POWER            = c["POWER"]
    REPEATS          = c["REPEATS"]
    OFF_MODE         = str(c["OFF_MODE"]).strip().lower()
    D1               = c["D1"]
    DS               = c["DS"]
    PROFILE_NS       = c["PROFILE_NS"]
    OFF_SCANS        = c["OFF_SCANS"]
    INTENSITY_MODE   = str(c["INTENSITY_MODE"]).strip().lower()
    fail = failer(RUN_LABEL)
    h = html_text

    if not re.match(r"^[A-Za-z0-9_-]+$", RUN_LABEL):
        fail("RUN_LABEL may contain only letters, digits, '-' and '_' (got '%s')." % RUN_LABEL)
        return
    if OFF_MODE not in ("start", "end", "both", "none"):
        fail("OFF_MODE must be 'start', 'end', 'both' or 'none' (got '%s')." % OFF_MODE)
        return
    if INTENSITY_MODE not in ("extreme", "max", "sum"):
        fail("INTENSITY_MODE must be 'extreme', 'max' or 'sum' (got '%s')." % INTENSITY_MODE)
        return
    if not isinstance(REPEATS, int) or REPEATS < 1:
        fail("REPEATS must be a positive integer.")
        return
    try:
        freqs = [float(f) for f in c["FREQS"]]
    except CATCH:
        fail("FREQS must be a list of frequencies in GHz.")
        return
    if not freqs:
        fail("FREQS is empty.")
        return
    try:
        float(POWER)
    except CATCH:
        fail("POWER must be a number (got %r)." % (POWER,))
        return
    if not check_power(fail, "POWER", float(POWER)):
        return

    # ---- Run plan: per set an optional OFF, one ON per frequency, an optional OFF ----
    per_set = []
    if OFF_MODE in ("start", "both"):
        per_set.append(("OFF", "start"))
    for f in freqs:
        per_set.append(("ON", f))
    if OFF_MODE in ("end", "both"):
        per_set.append(("OFF", "end"))
    points_per_set  = len(freqs)
    records_per_set = len(per_set)
    n_off_per_set   = records_per_set - points_per_set

    def set_tag(set_number):
        return ("set %d | " % set_number) if REPEATS > 1 else ""

    def make_plan(start_expno):
        plan = []
        for set_number in range(1, REPEATS + 1):
            base = start_expno + (set_number - 1) * records_per_set
            tag = set_tag(set_number)
            for i in range(records_per_set):
                kind, val = per_set[i]
                if kind == "OFF":
                    plan.append({
                        "expno": base + i, "set": set_number, "kind": "OFF", "label": val,
                        "freq": None, "d1": D1, "ns": OFF_SCANS, "awg": "stop",
                        "title": ("OFF (%s) | %s%s | %s | microwave off | D1 = %s s | %d scans"
                                  % (val, tag, SAMPLE, MAS_INFO, D1, OFF_SCANS)),
                        "what": "%sOFF %s" % (tag, val)})
                else:
                    cmdstr = 'cw %.3f %.2f' % (val, POWER)
                    plan.append({
                        "expno": base + i, "set": set_number, "kind": "ON", "label": "on",
                        "freq": val, "d1": D1, "ns": PROFILE_NS, "awg": cmdstr,
                        "title": ("freq profile | %s%s | %s | %s | D1 = %s s | %d scan(s)"
                                  % (tag, SAMPLE, MAS_INFO, cmdstr, D1, PROFILE_NS)),
                        "what": "%sON %.3f GHz" % (tag, val),
                        "skip": "%s%.3f GHz" % (tag, val), "last": "%.3f GHz" % val})
        return plan

    def dialog_rows(plan):
        def set_line(set_number):
            recs = [p for p in plan if p["set"] == set_number]
            offs = [p["expno"] for p in recs if p["kind"] == "OFF"]
            ons  = [p["expno"] for p in recs if p["kind"] == "ON"]
            parts = []
            if OFF_MODE in ("start", "both"):
                parts.append("OFF %d" % offs[0])
            parts.append("ON %d&#8211;%d" % (ons[0], ons[-1]))
            if OFF_MODE in ("end", "both"):
                parts.append("OFF %d" % offs[-1])
            pre = ("set %d: " % set_number) if REPEATS > 1 else ""
            return pre + ", then ".join(parts)

        shown = list(range(1, REPEATS + 1))
        if REPEATS > 6:
            shown = [1, 2, 3, None, REPEATS]
        plan_html = "<br>".join([("..." if n is None else set_line(n)) for n in shown])

        sf = sorted(freqs)
        gaps = [round((b - a) * 1000.0, 3) for a, b in zip(sf[:-1], sf[1:])]
        if not gaps:
            spacing = ""
        elif min(gaps) == max(gaps):
            spacing = ", %g MHz apart" % gaps[0]
        else:
            spacing = ", %g&#8211;%g MHz apart" % (min(gaps), max(gaps))
        freq_html = "%d per set, %.3f&#8211;%.3f GHz%s" % (points_per_set, sf[0], sf[-1], spacing)
        return [("Plan", plan_html), ("Frequencies", freq_html),
                ("Scans", "ON records NS %d, OFF records NS %d; D1 %s s, DS %d; power %.2f"
                 % (PROFILE_NS, OFF_SCANS, h(D1), DS, POWER))]

    def timing(plan, record_time):
        per_point_time = record_time(PROFILE_NS, D1)
        off_time       = record_time(OFF_SCANS, D1)
        total_time     = REPEATS * (per_point_time * points_per_set + off_time * n_off_per_set)
        note = ("ON ~%s per point, OFF ~%s each" % (fmt_dur(per_point_time), fmt_dur(off_time))
                if n_off_per_set else "ON ~%s per point" % fmt_dur(per_point_time))
        return total_time, note

    def header(run_id, ds_root, peak_str, started):
        return ("# fs run file (read by dnp_viewer.py and fs_rephase.py)\n"
                "# run_id = %s\n"
                "# label = %s\n"
                "# sample = %s\n"
                "# conditions = %s\n"
                "# dataset_dir = %s\n"
                "# off_mode = %s\n"
                "# peak_ppm = %s\n"
                "# window_ppm = %s\n"
                "# mode = %s\n"
                "# power = %.2f\n"
                "# d1 = %s\n"
                "# repeats = %d\n"
                "# started = %s\n"
                "# columns: expno, kind, label, freq_GHz, ns, finished, set\n"
                % (run_id, RUN_LABEL, SAMPLE, MAS_INFO, ds_root, OFF_MODE, peak_str,
                   repr(float(c["PEAK_WINDOW_PPM"])), INTENSITY_MODE, POWER, D1, REPEATS, started))

    run_records(c, {
        "noun": "frequency profile", "kind": "fs", "table": SETTINGS, "make_plan": make_plan,
        "dialog_rows": dialog_rows, "timing": timing, "header": header,
        "used": {"OFF_MODE": OFF_MODE, "FREQS": freqs},
        "settings_comments": lambda plan, record_time: [],
        "d1_column": False, "on_noun": "ON points",
        "start_desc": "%d set(s), OFF mode %s, %d ON points per set" % (REPEATS, OFF_MODE, points_per_set),
        "end_desc": "%d set(s), OFF mode %s" % (REPEATS, OFF_MODE)}, source)


def run_buildup(S, source=None):
    """Runs the build-up described by the settings dict S; source: the settings file, if any."""
    # ---- Settings ------------------------------------------------------------
    c = check_settings(S, BU_SETTINGS, kind_hint(S, "bu"))
    if c is None:
        return
    RUN_LABEL        = str(c["RUN_LABEL"]).strip()
    SAMPLE           = c["SAMPLE"]
    MAS_INFO         = c["MAS_INFO"]
    REPEATS          = c["REPEATS"]
    SERIES           = str(c["SERIES"]).strip().lower()
    DS               = c["DS"]
    INTENSITY_MODE   = str(c["INTENSITY_MODE"]).strip().lower()
    fail = failer(RUN_LABEL)

    if not re.match(r"^[A-Za-z0-9_-]+$", RUN_LABEL):
        fail("RUN_LABEL may contain only letters, digits, '-' and '_' (got '%s')." % RUN_LABEL)
        return
    if SERIES not in BU_SERIES:
        fail("SERIES must be one of %s (got '%s')." % (", ".join(["'%s'" % s for s in BU_SERIES]), SERIES))
        return
    if INTENSITY_MODE not in ("extreme", "max", "sum"):
        fail("INTENSITY_MODE must be 'extreme', 'max' or 'sum' (got '%s')." % INTENSITY_MODE)
        return
    if not isinstance(REPEATS, int) or REPEATS < 1:
        fail("REPEATS must be a positive integer.")
        return

    def num(x):
        v = float(x)
        return int(v) if v == int(v) else v
    try:
        d1s = [num(x) for x in c["D1_LIST"]]
    except CATCH:
        fail("D1_LIST must be a list of build-up times in s.")
        return
    if not d1s:
        fail("D1_LIST is empty.")
        return
    if min(d1s) <= 0:
        fail("D1_LIST has a value that is not positive: %s." % min(d1s))
        return

    def ns_list(name, val):
        """val as one NS per D1, or None after an error box."""
        vals = val if isinstance(val, (list, tuple)) else [val] * len(d1s)
        if len(vals) != len(d1s):
            fail("%s has %d values, but D1_LIST has %d." % (name, len(vals), len(d1s)))
            return None
        out = []
        for v in vals:
            try:
                ok = float(v) == int(v) and int(v) >= 1
            except CATCH:
                ok = False
            if not ok:
                fail("%s must hold whole numbers of scans, 1 or more (got %r)." % (name, v))
                return None
            out.append(int(v))
        return out
    ns_on = ns_list("NS_LIST", c["NS_LIST"])
    if ns_on is None:
        return
    has_on, has_off = SERIES != "off", SERIES != "on"
    ns_off = ns_on
    if c["OFF_NS_LIST"] is not None:
        ns_off = ns_list("OFF_NS_LIST", c["OFF_NS_LIST"])
        if ns_off is None:
            return
    FREQ, POWER = c["FREQ"], c["POWER"]
    FREQS = c["FREQS"]
    FREQ_ORDER = str(c["FREQ_ORDER"]).strip().lower()
    conds = None                                 # with FREQS: [(GHz, power, 'cw' command)]
    if FREQS is not None:
        if SERIES != "on":
            fail("FREQS (several frequencies) works with SERIES 'on' only (got '%s'); the OFF "
                 "build-up does not depend on the frequency, so run it separately." % SERIES)
            return
        if FREQ is not None:
            fail("set FREQ (one frequency) or FREQS (several), not both.")
            return
        if FREQ_ORDER not in ("by_d1", "by_freq"):
            fail("FREQ_ORDER must be 'by_d1' or 'by_freq' (got '%s')." % FREQ_ORDER)
            return
        if not isinstance(FREQS, (list, tuple)) or not FREQS:
            fail("FREQS must be a list of frequencies in GHz, e.g. [526.008, 525.985].")
            return
        conds = []
        for x in FREQS:
            pair = isinstance(x, (list, tuple))
            try:
                if pair:
                    if len(x) != 2:
                        raise ValueError("not a pair")
                    f, p = float(x[0]), float(x[1])
                else:
                    f, p = float(x), float(POWER)
            except CATCH:
                fail("FREQS entry %r: each entry is a frequency in GHz, which gets POWER, or a "
                     "(frequency, power) pair%s." % (x, "" if pair else "; POWER is not set (got %r)" % (POWER,)))
                return
            if not check_power(fail, "the power of FREQS entry %r" % (x,), p):
                return
            if [q for q in conds if abs(q[0] - f) < 5e-7 and abs(q[1] - p) < 5e-7]:
                fail("FREQS has %.4f GHz at power %g twice." % (f, p))
                return
            conds.append((f, p, 'cw %.3f %.3f' % (f, p)))
    if has_on and conds is None:
        for name in ("FREQ", "POWER"):
            try:
                float(c[name])
            except CATCH:
                fail("SERIES '%s' has ON records: set %s, %s (got %r)."
                     % (SERIES, name, "the mm-wave frequency in GHz" if name == "FREQ"
                        else "the second argument of the AWG 'cw' command", c[name]))
                return
        FREQ, POWER = float(FREQ), float(POWER)
        if not check_power(fail, "POWER", POWER):
            return

    # ---- Run plan ---------------------------------------------------------------
    n = len(d1s)
    if SERIES == "on":
        per_set = [("ON", i) for i in range(n)]
    elif SERIES == "off":
        per_set = [("OFF", i) for i in range(n)]
    elif SERIES == "interleaved":
        per_set = []
        for i in range(n):
            per_set += [("ON", i), ("OFF", i)]
    elif SERIES == "on_then_off":
        per_set = [("ON", i) for i in range(n)] + [("OFF", i) for i in range(n)]
    else:
        per_set = [("OFF", i) for i in range(n)] + [("ON", i) for i in range(n)]
    cmdstr = ('cw %.3f %.2f' % (FREQ, POWER)) if (has_on and conds is None) else None

    def set_tag(set_number):
        return ("set %d | " % set_number) if REPEATS > 1 else ""

    nf = len(conds) if conds else 0
    same_power = bool(conds) and len(set([q[1] for q in conds])) == 1

    def cond_text(k):
        """The frequency (and power, if they differ) of condition k, for titles and the log."""
        f, p, cmd = conds[k]
        return ("%.3f GHz" % f) if same_power else ("%.3f GHz, power %g" % (f, p))

    def make_plan_freqs(start_expno):
        """FREQS: one set per frequency (and repeat), set = (repeat - 1) * nf + k + 1; expnos in
        acquisition order, one block of nf * n per repeat."""
        plan = []
        for rep in range(1, REPEATS + 1):
            base = start_expno + (rep - 1) * nf * n
            if FREQ_ORDER == "by_d1":
                order = [(i, k) for i in range(n) for k in range(nf)]
            else:
                order = [(i, k) for k in range(nf) for i in range(n)]
            for j, (i, k) in enumerate(order):
                d1, ns = d1s[i], ns_on[i]
                f, p, cmd = conds[k]
                set_number = (rep - 1) * nf + k + 1
                tag = ("repeat %d | " % rep) if REPEATS > 1 else ""
                plan.append({
                    "expno": base + j, "set": set_number, "kind": "ON", "label": "on",
                    "freq": f, "d1": d1, "ns": ns, "awg": cmd,
                    "title": ("build-up | %s%s | %s | %s | D1 = %s s | %d scan(s)"
                              % (tag, SAMPLE, MAS_INFO, cmd, d1, ns)),
                    "what": "%sON %s D1 %s s" % (tag, cond_text(k), d1),
                    "skip": "%sON %s at D1 %s s" % (tag, cond_text(k), d1),
                    "last": "%s, D1 %s s" % (cond_text(k), d1)})
        return plan

    def make_plan(start_expno):
        if conds:
            return make_plan_freqs(start_expno)
        plan = []
        for set_number in range(1, REPEATS + 1):
            base = start_expno + (set_number - 1) * len(per_set)
            tag = set_tag(set_number)
            for j, (kind, i) in enumerate(per_set):
                d1 = d1s[i]
                if kind == "OFF":
                    ns = ns_off[i]
                    plan.append({
                        "expno": base + j, "set": set_number, "kind": "OFF", "label": "off",
                        "freq": None, "d1": d1, "ns": ns, "awg": "stop",
                        "title": ("build-up | %s%s | %s | microwave off | D1 = %s s | %d scan(s)"
                                  % (tag, SAMPLE, MAS_INFO, d1, ns)),
                        "what": "%sOFF D1 %s s" % (tag, d1)})
                else:
                    ns = ns_on[i]
                    plan.append({
                        "expno": base + j, "set": set_number, "kind": "ON", "label": "on",
                        "freq": FREQ, "d1": d1, "ns": ns, "awg": cmdstr,
                        "title": ("build-up | %s%s | %s | %s | D1 = %s s | %d scan(s)"
                                  % (tag, SAMPLE, MAS_INFO, cmdstr, d1, ns)),
                        "what": "%sON D1 %s s" % (tag, d1),
                        "skip": "%sON at D1 %s s" % (tag, d1), "last": "D1 %s s" % d1})
        return plan

    def d1_ns_html(nss):
        return ", ".join(["%s&nbsp;s&nbsp;&#215;&nbsp;%d" % (d1, k) for d1, k in zip(d1s, nss)])

    def dialog_rows_freqs(plan):
        lines = []
        for rep in range(1, REPEATS + 1):
            recs = [p for p in plan if (p["set"] - 1) // nf == rep - 1]
            body = ("%d build-ups, %s: %d&#8211;%d"
                    % (nf, "at each D1 every frequency in turn" if FREQ_ORDER == "by_d1"
                       else "one frequency after the other", recs[0]["expno"], recs[-1]["expno"]))
            lines.append((("repeat %d: " % rep) if REPEATS > 1 else "") + body)
        if len(lines) > 6:
            lines = lines[:3] + ["..."] + lines[-1:]
        out = [("Plan", "<br>".join(lines))]
        out.append(("mm-wave", "<br>".join(
            ["set %d: %.3f GHz, power %g (AWG '%s')" % (k + 1, q[0], q[1], q[2]) for k, q in enumerate(conds)]
            + (["repeats: sets %d&#8211;%d, the same frequencies in the same order" % (nf + 1, nf * REPEATS)]
               if REPEATS > 1 else []))))
        out.append(("D1 &#215; NS", d1_ns_html(ns_on)))
        out.append(("Scans", "%d build-up times per frequency, %s&#8211;%s s, in this order; DS %d. "
                    "The pulse program must saturate before D1." % (n, min(d1s), max(d1s), DS)))
        return out

    def dialog_rows(plan):
        if conds:
            return dialog_rows_freqs(plan)

        def set_line(set_number):
            recs = [p for p in plan if p["set"] == set_number]
            first, last = recs[0]["expno"], recs[-1]["expno"]
            if SERIES == "interleaved":
                body = "ON and OFF at each D1, ON first: %d&#8211;%d" % (first, last)
            elif SERIES in ("on", "off"):
                body = "%s %d&#8211;%d" % (SERIES.upper(), first, last)
            else:
                k1 = recs[0]["kind"]
                a = [p["expno"] for p in recs if p["kind"] == k1]
                b = [p["expno"] for p in recs if p["kind"] != k1]
                k2 = "OFF" if k1 == "ON" else "ON"
                body = "%s %d&#8211;%d, then %s %d&#8211;%d" % (k1, a[0], a[-1], k2, b[0], b[-1])
            pre = ("set %d: " % set_number) if REPEATS > 1 else ""
            return pre + body

        shown = list(range(1, REPEATS + 1))
        if REPEATS > 6:
            shown = [1, 2, 3, None, REPEATS]
        rows = [("Plan", "<br>".join([("..." if k is None else set_line(k)) for k in shown]))]
        mw = []
        if has_on:
            mw.append("ON records: %.3f GHz, power %.2f (AWG '%s')" % (FREQ, POWER, cmdstr))
        if has_off:
            mw.append("OFF records: microwave off (AWG 'stop')")
        rows.append(("mm-wave", "<br>".join(mw)))
        same = (not has_on) or (not has_off) or ns_on == ns_off
        if same:
            rows.append(("D1 &#215; NS", d1_ns_html(ns_on if has_on else ns_off)))
        else:
            rows.append(("D1 &#215; NS", "ON: %s<br>OFF: %s" % (d1_ns_html(ns_on), d1_ns_html(ns_off))))
        rows.append(("Scans", "%d build-up times per set, %s&#8211;%s s, in this order; DS %d. "
                     "The pulse program must saturate before D1." % (n, min(d1s), max(d1s), DS)))
        return rows

    def timing(plan, record_time):
        times = [record_time(p["ns"], p["d1"]) for p in plan]
        total = sum(times)
        k = times.index(max(times))
        return total, ("longest record ~%s (D1 %s s, NS %d)"
                       % (fmt_dur(times[k]), plan[k]["d1"], plan[k]["ns"]))

    def header(run_id, ds_root, peak_str, started):
        return ("# fs run file (read by dnp_viewer.py and fs_rephase.py)\n"
                "# type = buildup\n"
                "# run_id = %s\n"
                "# label = %s\n"
                "# sample = %s\n"
                "# conditions = %s\n"
                "# dataset_dir = %s\n"
                "# series = %s\n"
                "# freq_GHz = %s\n"
                "# power = %s\n"
                "# peak_ppm = %s\n"
                "# window_ppm = %s\n"
                "# mode = %s\n"
                "# ds = %s\n"
                "# repeats = %d\n"
                "# started = %s\n"
                "# columns: expno, kind, label, freq_GHz, ns, finished, set, d1_s\n"
                % (run_id, RUN_LABEL, SAMPLE, MAS_INFO, ds_root, SERIES,
                   ("%.4f" % FREQ) if (has_on and not conds) else "-",
                   ("%.2f" % POWER) if (has_on and not conds) else "-",
                   peak_str, repr(float(c["PEAK_WINDOW_PPM"])), INTENSITY_MODE, DS, REPEATS, started)
                ).replace("# columns:", freqs_header() + "# columns:", 1)

    def freqs_header():
        """With FREQS: the frequency and power of each set, for dnp_viewer.py ('' without)."""
        if not conds:
            return ""
        return ("# freq_order = %s\n# set_cw = %s\n"
                % (FREQ_ORDER, "; ".join(["%d %.4f %g" % ((rep - 1) * nf + k + 1, q[0], q[1])
                                          for rep in range(1, REPEATS + 1)
                                          for k, q in enumerate(conds)])))

    def settings_comments(plan, record_time):
        out = ["# planned records (expno, set, kind, D1 s, NS, expected s; read by dnp_viewer.py):"]
        for p in plan:
            out.append("# record: %d %d %s %s %d %d" % (p["expno"], p["set"], p["kind"], p["d1"], p["ns"],
                                                        int(round(record_time(p["ns"], p["d1"])))))
        return out

    run_records(c, {
        "noun": "build-up", "kind": "bu", "table": BU_SETTINGS, "make_plan": make_plan,
        "dialog_rows": dialog_rows, "timing": timing, "header": header,
        "used": {"SERIES": SERIES, "FREQ": FREQ, "POWER": POWER, "D1_LIST": d1s,
                 "NS_LIST": ns_on, "OFF_NS_LIST": ns_off if has_off else c["OFF_NS_LIST"],
                 "FREQS": [(q[0], q[1]) for q in conds] if conds else None,
                 "FREQ_ORDER": FREQ_ORDER},
        "settings_comments": settings_comments,
        "d1_column": True, "on_noun": "ON records",
        "start_desc": (("%d frequencies x %d repeat(s), %s, %d build-up times each"
                        % (nf, REPEATS, FREQ_ORDER, n)) if conds else
                       "%d set(s), series %s, %d build-up times per set" % (REPEATS, SERIES, n)),
        "end_desc": (("%d frequencies x %d repeat(s)" % (nf, REPEATS)) if conds else
                     "%d set(s), series %s" % (REPEATS, SERIES))}, source)


def run_decay(S, source=None):
    """Runs the decay described by the settings dict S; source: the settings file, if any.
    Per set: 'cw' and POLARIZE_TIME s of polarization, ending with a reference record (ON,
    NS 1); 'stop'; then one record (OFF, NS 1) per target time after the microwaves went off,
    each with the D1 that brings its pulse to that time."""
    # ---- Settings ------------------------------------------------------------
    c = check_settings(S, DECAY_SETTINGS, kind_hint(S, "decay"))
    if c is None:
        return
    RUN_LABEL        = str(c["RUN_LABEL"]).strip()
    SAMPLE           = c["SAMPLE"]
    MAS_INFO         = c["MAS_INFO"]
    REPEATS          = c["REPEATS"]
    INTENSITY_MODE   = str(c["INTENSITY_MODE"]).strip().lower()
    AWG_SETTLE       = c["AWG_SETTLE"]
    fail = failer(RUN_LABEL)

    if not re.match(r"^[A-Za-z0-9_-]+$", RUN_LABEL):
        fail("RUN_LABEL may contain only letters, digits, '-' and '_' (got '%s')." % RUN_LABEL)
        return
    if INTENSITY_MODE not in ("extreme", "max", "sum"):
        fail("INTENSITY_MODE must be 'extreme', 'max' or 'sum' (got '%s')." % INTENSITY_MODE)
        return
    if not isinstance(REPEATS, int) or REPEATS < 1:
        fail("REPEATS must be a positive integer.")
        return
    nums = {}
    for name in ("FREQ", "POWER", "POLARIZE_TIME", "FLIP_DEG", "ZG_LATENCY", "MIN_D1"):
        try:
            nums[name] = float(c[name])
        except CATCH:
            fail("%s must be a number (got %r)." % (name, c[name]))
            return
    FREQ, POWER, POLARIZE_TIME = nums["FREQ"], nums["POWER"], nums["POLARIZE_TIME"]
    FLIP_DEG, ZG_LATENCY, MIN_D1 = nums["FLIP_DEG"], nums["ZG_LATENCY"], nums["MIN_D1"]
    if not check_power(fail, "POWER", POWER):
        return
    if POLARIZE_TIME <= 0:
        fail("POLARIZE_TIME must be positive.")
        return
    if not 0 < FLIP_DEG < 180:
        fail("FLIP_DEG must be between 0 and 180 (got %s)." % FLIP_DEG)
        return

    def num(x):
        v = float(x)
        return int(v) if v == int(v) else v
    try:
        targets = [num(x) for x in c["TIMES_LIST"]]
    except CATCH:
        fail("TIMES_LIST must be a list of times in s after the microwaves go off.")
        return
    if not targets:
        fail("TIMES_LIST is empty.")
        return
    if min(targets) <= 0 or [t for a, t in zip(targets[:-1], targets[1:]) if t <= a]:
        fail("TIMES_LIST must hold positive times in increasing order.")
        return
    cmdstr = 'cw %.3f %.2f' % (FREQ, POWER)
    c = dict(c, DS=0, MAX_CONSEC_SKIPS=1)        # the engine's settings that decays do not have
    rec_s = c["EST_OVERHEAD"] + c["SCAN_OVERHEAD"] + c["POST_ACQ_PAD"]   # s per record besides D1

    def set_tag(set_number):
        return ("set %d | " % set_number) if REPEATS > 1 else ""

    def make_plan(start_expno):
        plan = []
        per_set = len(targets) + 1
        for set_number in range(1, REPEATS + 1):
            base = start_expno + (set_number - 1) * per_set
            tag = set_tag(set_number)
            plan.append({
                "expno": base, "set": set_number, "kind": "ON", "label": "ref", "freq": FREQ,
                "d1": num(POLARIZE_TIME), "ns": 1, "awg": cmdstr, "role": "ref", "target": 0,
                "title": ("decay reference | %s%s | %s | %s | %g s polarization | 1 scan"
                          % (tag, SAMPLE, MAS_INFO, cmdstr, POLARIZE_TIME)),
                "what": "%sreference after %g s with '%s'" % (tag, POLARIZE_TIME, cmdstr),
                "skip": "", "last": ""})
            for j, t in enumerate(targets):
                plan.append({
                    "expno": base + 1 + j, "set": set_number, "kind": "OFF", "label": "decay", "freq": None,
                    "d1": t, "ns": 1, "awg": None, "role": "decay", "target": t,
                    "title": ("decay | %s%s | %s | microwave off | t = %s s after it went off | 1 scan"
                              % (tag, SAMPLE, MAS_INFO, t)),
                    "what": "%sdecay t = %s s" % (tag, t)})
        return plan

    def expected(p):
        """Expected duration of a record, for the time estimate and the viewer's expected end."""
        if p["role"] == "ref":
            return POLARIZE_TIME + AWG_SETTLE + rec_s
        i = targets.index(p["target"])
        return max(p["target"] - (targets[i - 1] if i else 0), MIN_D1 + rec_s)

    def dialog_rows(plan):
        shown = list(range(1, REPEATS + 1))
        if REPEATS > 6:
            shown = [1, 2, 3, None, REPEATS]
        lines = []
        for k in shown:
            if k is None:
                lines.append("...")
                continue
            recs = [p for p in plan if p["set"] == k]
            lines.append("%sreference %d, then decay %d&#8211;%d"
                         % (("set %d: " % k) if REPEATS > 1 else "", recs[0]["expno"], recs[1]["expno"],
                            recs[-1]["expno"]))
        gaps = [b - a for a, b in zip([0] + targets[:-1], targets)]
        tight = [t for t, g in zip(targets, gaps) if g < rec_s + MIN_D1 + ZG_LATENCY]
        tx = ", ".join(["%s" % t for t in targets])
        if tight:
            tx += ("<br><font color='#a04000'>%d target(s) less than about %d s after the one before "
                   "(%s s): each comes as soon as the record before it is done</font>"
                   % (len(tight), int(rec_s + MIN_D1 + ZG_LATENCY), ", ".join(["%s" % t for t in tight])))
        return [("Plan", "<br>".join(lines)),
                ("mm-wave", "AWG '%s', reference record after %g s (%s), then 'stop'"
                 % (cmdstr, POLARIZE_TIME, fmt_dur(POLARIZE_TIME))),
                ("Times", "%d per set, s after the microwaves go off: %s" % (len(targets), tx)),
                ("Scans", "NS 1, DS 0 on every record; D1 set for each record to reach its time. "
                          "Flip angle %g&#176; (from the template; for the viewer's correction); "
                          "no saturation in the pulse program." % FLIP_DEG)]

    def timing(plan, record_time):
        total = sum([expected(p) for p in plan])
        return total, ("per set: %s polarizing, then %s of decay"
                       % (fmt_dur(POLARIZE_TIME), fmt_dur(targets[-1])))

    def header(run_id, ds_root, peak_str, started):
        return ("# fs run file (read by dnp_viewer.py and fs_rephase.py)\n"
                "# type = decay\n"
                "# run_id = %s\n"
                "# label = %s\n"
                "# sample = %s\n"
                "# conditions = %s\n"
                "# dataset_dir = %s\n"
                "# freq_GHz = %.4f\n"
                "# power = %.2f\n"
                "# polarize_s = %s\n"
                "# flip_deg = %s\n"
                "# peak_ppm = %s\n"
                "# window_ppm = %s\n"
                "# mode = %s\n"
                "# repeats = %d\n"
                "# started = %s\n"
                "# t_s: time of the record's pulse after the microwaves went off (end of acquisition\n"
                "#      less AQ); target_s: the time aimed at\n"
                "# columns: expno, kind, label, freq_GHz, ns, finished, set, d1_s, t_s, target_s\n"
                % (run_id, RUN_LABEL, SAMPLE, MAS_INFO, ds_root, FREQ, POWER, POLARIZE_TIME, FLIP_DEG,
                   peak_str, repr(float(c["PEAK_WINDOW_PPM"])), INTENSITY_MODE, REPEATS, started))

    def settings_comments(plan, record_time):
        out = ["# planned records (expno, set, kind, D1 or target s, NS, expected s; read by dnp_viewer.py):"]
        for p in plan:
            out.append("# record: %d %d %s %s %d %d" % (p["expno"], p["set"], p["kind"], p["d1"], 1,
                                                        int(round(expected(p)))))
        return out

    def row_extra(rec):
        return "\t%.3f\t%s" % (rec.get("t", float("nan")), rec["target"])

    state = {"t_cw": None, "t_off": None, "lat": []}

    def latency():
        lat = sorted(state["lat"])
        if not lat:
            return ZG_LATENCY
        return lat[len(lat) // 2]

    def aq_s(ops, expno):
        try:
            return float(ops["acqus_param"](expno, "TD")) / (2.0 * float(ops["acqus_param"](expno, "SW_h")))
        except CATCH:
            return 0.0

    def runner(rec, ops):
        """Acquires one record of a decay: the reference ('cw', polarization, record, 'stop'),
        or a decay record with the D1 that brings its pulse to its target time."""
        expno = rec["expno"]
        if rec["role"] == "ref":
            if not ops["awg"](cmdstr):
                raise RunAbort("could not send '%s' to the AWG to polarize (set %d)" % (cmdstr, rec["set"]))
            state["t_cw"] = time.time()
            SLEEP(AWG_SETTLE)
            t_calc = time.time()
            d1 = max(MIN_D1, POLARIZE_TIME - (t_calc - state["t_cw"]) - latency())
        else:
            t_calc = time.time()
            d1 = rec["target"] - (t_calc - state["t_off"]) - latency()
            if d1 < MIN_D1:
                ops["log"]("expno %d: target t = %s s cannot be met (%.1f s late with D1 = %s s)"
                           % (expno, rec["target"], MIN_D1 - d1, MIN_D1))
                d1 = MIN_D1
        d1 = round(d1, 3)
        rec["d1"] = d1
        ops["new_record"](expno, 1, d1, rec["title"])
        t_fin = ops["acquire"](expno, 1, d1, rec["what"])
        t_pulse = t_fin - aq_s(ops, expno)
        state["lat"].append(t_pulse - t_calc - d1)
        if rec["role"] == "ref":
            if not ops["awg"]("stop"):
                raise RunAbort("could not send 'stop' to the AWG after the reference record (expno %d)" % expno)
            state["t_off"] = time.time()
            rec["t"] = t_pulse - state["t_off"]
            ops["log"]("set %d: microwave off ('stop'); the reference pulse came %.0f s after 'cw' "
                       "and %.1f s before 'stop'" % (rec["set"], t_pulse - state["t_cw"], -rec["t"]))
        else:
            rec["t"] = t_pulse - state["t_off"]
            ops["log"]("expno %d: pulse at t = %.1f s after the microwave went off (target %s s)"
                       % (expno, rec["t"], rec["target"]))
        return t_fin

    run_records(c, {
        "noun": "decay", "kind": "decay", "table": DECAY_SETTINGS, "make_plan": make_plan,
        "dialog_rows": dialog_rows, "timing": timing, "header": header,
        "used": {"FREQ": FREQ, "POWER": POWER, "POLARIZE_TIME": POLARIZE_TIME, "TIMES_LIST": targets,
                 "FLIP_DEG": FLIP_DEG, "ZG_LATENCY": ZG_LATENCY, "MIN_D1": MIN_D1},
        "settings_comments": settings_comments, "record_runner": runner, "row_extra": row_extra,
        "d1_column": True, "on_noun": "ON records",
        "start_desc": "%d set(s), %g s polarization, %d decay times per set" % (REPEATS, POLARIZE_TIME,
                                                                              len(targets)),
        "end_desc": "%d set(s), %d decay times per set" % (REPEATS, len(targets))}, source)


def run_powdep(S, source=None):
    """Runs the power dependence described by the settings dict S: per set an optional OFF,
    one ON record at FREQ per drive voltage, an optional OFF (as a profile with OFF_MODE)."""
    # ---- Settings ------------------------------------------------------------
    c = check_settings(S, POWDEP_SETTINGS, kind_hint(S, "powdep"))
    if c is None:
        return
    RUN_LABEL        = str(c["RUN_LABEL"]).strip()
    SAMPLE           = c["SAMPLE"]
    MAS_INFO         = c["MAS_INFO"]
    REPEATS          = c["REPEATS"]
    OFF_MODE         = str(c["OFF_MODE"]).strip().lower()
    D1               = c["D1"]
    DS               = c["DS"]
    ON_SCANS         = c["ON_SCANS"]
    OFF_SCANS        = c["OFF_SCANS"]
    INTENSITY_MODE   = str(c["INTENSITY_MODE"]).strip().lower()
    fail = failer(RUN_LABEL)
    h = html_text

    if not re.match(r"^[A-Za-z0-9_-]+$", RUN_LABEL):
        fail("RUN_LABEL may contain only letters, digits, '-' and '_' (got '%s')." % RUN_LABEL)
        return
    if OFF_MODE not in ("start", "end", "both", "none"):
        fail("OFF_MODE must be 'start', 'end', 'both' or 'none' (got '%s')." % OFF_MODE)
        return
    if INTENSITY_MODE not in ("extreme", "max", "sum"):
        fail("INTENSITY_MODE must be 'extreme', 'max' or 'sum' (got '%s')." % INTENSITY_MODE)
        return
    if not isinstance(REPEATS, int) or REPEATS < 1:
        fail("REPEATS must be a positive integer.")
        return
    try:
        FREQ = float(c["FREQ"])
    except CATCH:
        fail("FREQ must be the mm-wave frequency in GHz (got %r)." % (c["FREQ"],))
        return

    # ---- Calibration and drive voltages ------------------------------------------
    cal_path = c["POWER_CAL"] or POWER_CAL_PATH
    try:
        cal = load_power_cal(cal_path)
    except CATCH as ex:
        fail("The power calibration %s could not be used: %s." % (cal_path, ex))
        return
    v_lo = cal["v"][0]
    if (c["VOLTAGES"] is None) == (c["POWER_FRACTIONS"] is None):
        fail("Set either VOLTAGES (AWG drive voltages in V) or POWER_FRACTIONS (fractions of "
             "the power at %g V), not both and not neither." % MAX_AWG_VOLTAGE)
        return
    volts = []
    if c["VOLTAGES"] is not None:
        try:
            given = [float(x) for x in c["VOLTAGES"]]
        except CATCH:
            fail("VOLTAGES must be a list of AWG drive voltages in V.")
            return
        for v in given:
            if not check_power(fail, "Each of VOLTAGES", v):
                return
            if v < v_lo - 1e-9:
                fail("VOLTAGES: %g V is below the lowest point of the calibration (%g V in %s), so "
                     "its power is not known. Add calibration points below it to go lower."
                     % (v, v_lo, cal_path))
                return
            volts.append(round(v, 3))
    else:
        f_lo = power_of_voltage(cal, v_lo) / cal["p_full"]
        try:
            fracs = [float(x) for x in c["POWER_FRACTIONS"]]
        except CATCH:
            fail("POWER_FRACTIONS must be a list of fractions of the power at %g V." % MAX_AWG_VOLTAGE)
            return
        for f in fracs:
            if not f_lo - 1e-9 <= f <= 1.0 + 1e-9:
                fail("POWER_FRACTIONS: %g is outside what the calibration covers, %.3f (at %g V) to 1 "
                     "(at %g V)." % (f, f_lo, v_lo, MAX_AWG_VOLTAGE))
                return
            volts.append(round(min(MAX_AWG_VOLTAGE, max(v_lo, voltage_of_fraction(cal, f))), 3))
    if not volts:
        fail("%s is empty." % ("VOLTAGES" if c["VOLTAGES"] is not None else "POWER_FRACTIONS"))
        return

    def frac(v):
        return power_of_voltage(cal, v) / cal["p_full"]

    def mw(v):
        return power_of_voltage(cal, v)
    cal_freq = ("%.3f GHz" % cal["freq"]) if cal["freq"] is not None else "the calibration frequency"

    # ---- Run plan: per set an optional OFF, one ON per voltage, an optional OFF ----
    per_set = []
    if OFF_MODE in ("start", "both"):
        per_set.append(("OFF", "start"))
    for v in volts:
        per_set.append(("ON", v))
    if OFF_MODE in ("end", "both"):
        per_set.append(("OFF", "end"))
    points_per_set  = len(volts)
    records_per_set = len(per_set)
    n_off_per_set   = records_per_set - points_per_set

    def set_tag(set_number):
        return ("set %d | " % set_number) if REPEATS > 1 else ""

    def make_plan(start_expno):
        plan = []
        for set_number in range(1, REPEATS + 1):
            base = start_expno + (set_number - 1) * records_per_set
            tag = set_tag(set_number)
            for i in range(records_per_set):
                kind, val = per_set[i]
                if kind == "OFF":
                    plan.append({
                        "expno": base + i, "set": set_number, "kind": "OFF", "label": val,
                        "freq": None, "volt": None, "d1": D1, "ns": OFF_SCANS, "awg": "stop",
                        "title": ("OFF (%s) | %s%s | %s | microwave off | D1 = %s s | %d scans"
                                  % (val, tag, SAMPLE, MAS_INFO, D1, OFF_SCANS)),
                        "what": "%sOFF %s" % (tag, val)})
                else:
                    cmdstr = 'cw %.3f %.3f' % (FREQ, val)
                    plan.append({
                        "expno": base + i, "set": set_number, "kind": "ON", "label": "on",
                        "freq": FREQ, "volt": val, "d1": D1, "ns": ON_SCANS, "awg": cmdstr,
                        "title": ("power dep | %s%s | %s | %s | %.3f of full power | D1 = %s s | %d scan(s)"
                                  % (tag, SAMPLE, MAS_INFO, cmdstr, frac(val), D1, ON_SCANS)),
                        "what": "%sON %.3f V" % (tag, val),
                        "skip": "%s%.3f V" % (tag, val), "last": "%.3f V" % val})
        return plan

    def dialog_rows(plan):
        def set_line(set_number):
            recs = [p for p in plan if p["set"] == set_number]
            offs = [p["expno"] for p in recs if p["kind"] == "OFF"]
            ons  = [p["expno"] for p in recs if p["kind"] == "ON"]
            parts = []
            if OFF_MODE in ("start", "both"):
                parts.append("OFF %d" % offs[0])
            parts.append("ON %d&#8211;%d" % (ons[0], ons[-1]))
            if OFF_MODE in ("end", "both"):
                parts.append("OFF %d" % offs[-1])
            pre = ("set %d: " % set_number) if REPEATS > 1 else ""
            return pre + ", then ".join(parts)

        shown = list(range(1, REPEATS + 1))
        if REPEATS > 6:
            shown = [1, 2, 3, None, REPEATS]
        plan_html = "<br>".join([("..." if n is None else set_line(n)) for n in shown])
        items = ["%.3f V (%.2f, %.1f mW)" % (v, frac(v), mw(v)) for v in volts]
        lines = [", ".join(items[i:i + 4]) for i in range(0, len(items), 4)]
        power_html = ("%d per set, in this order: drive voltage (fraction of the power at %g V, "
                      "mW at %s)<br>%s" % (points_per_set, MAX_AWG_VOLTAGE, h(cal_freq), "<br>".join(lines)))
        return [("Plan", plan_html),
                ("mm-wave", "%.3f GHz, AWG 'cw %.3f &lt;voltage&gt;'; calibration %s"
                 % (FREQ, FREQ, h(cal_path))),
                ("Powers", power_html),
                ("Scans", "ON records NS %d, OFF records NS %d; D1 %s s, DS %d"
                 % (ON_SCANS, OFF_SCANS, h(D1), DS))]

    def timing(plan, record_time):
        per_point_time = record_time(ON_SCANS, D1)
        off_time       = record_time(OFF_SCANS, D1)
        total_time     = REPEATS * (per_point_time * points_per_set + off_time * n_off_per_set)
        note = ("ON ~%s per point, OFF ~%s each" % (fmt_dur(per_point_time), fmt_dur(off_time))
                if n_off_per_set else "ON ~%s per point" % fmt_dur(per_point_time))
        return total_time, note

    def header(run_id, ds_root, peak_str, started):
        return ("# fs run file (read by dnp_viewer.py and fs_rephase.py)\n"
                "# type = powdep\n"
                "# run_id = %s\n"
                "# label = %s\n"
                "# sample = %s\n"
                "# conditions = %s\n"
                "# dataset_dir = %s\n"
                "# off_mode = %s\n"
                "# peak_ppm = %s\n"
                "# window_ppm = %s\n"
                "# mode = %s\n"
                "# freq_GHz = %.4f\n"
                "# full_power_V = %g\n"
                "# cal_file = %s\n"
                "# cal_freq_GHz = %s\n"
                "# cal_mV = %s\n"
                "# cal_mW = %s\n"
                "# d1 = %s\n"
                "# repeats = %d\n"
                "# started = %s\n"
                "# drive_V: second argument of 'cw'; the viewer converts it to power with cal_mV/cal_mW\n"
                "# columns: expno, kind, label, freq_GHz, ns, finished, set, drive_V\n"
                % (run_id, RUN_LABEL, SAMPLE, MAS_INFO, ds_root, OFF_MODE, peak_str,
                   repr(float(c["PEAK_WINDOW_PPM"])), INTENSITY_MODE, FREQ, MAX_AWG_VOLTAGE, cal_path,
                   "none" if cal["freq"] is None else repr(cal["freq"]),
                   ",".join(["%g" % (v * 1000.0) for v in cal["v"]]), ",".join(["%g" % p for p in cal["p"]]),
                   D1, REPEATS, started))

    def row_extra(rec):
        return ("\t%.3f" % rec["volt"]) if rec["kind"] == "ON" else "\t-"

    run_records(c, {
        "noun": "power dependence", "kind": "powdep", "table": POWDEP_SETTINGS, "make_plan": make_plan,
        "dialog_rows": dialog_rows, "timing": timing, "header": header,
        "used": {"OFF_MODE": OFF_MODE, "FREQ": FREQ, "VOLTAGES": volts,
                 "POWER_FRACTIONS": c["POWER_FRACTIONS"], "POWER_CAL": cal_path},
        "settings_comments": lambda plan, record_time: [],
        "row_extra": row_extra,
        "d1_column": False, "on_noun": "ON points",
        "start_desc": "%d set(s), OFF mode %s, %d powers per set at %.3f GHz"
                      % (REPEATS, OFF_MODE, points_per_set, FREQ),
        "end_desc": "%d set(s), OFF mode %s" % (REPEATS, OFF_MODE)}, source)


def run_chirp2d(S, source=None):
    """Runs the chirp grid described by the settings dict S: per set an optional OFF, one CW
    record, one ON record per chirp (width x time), an optional OFF."""
    # ---- Settings ------------------------------------------------------------
    c = check_settings(S, CHIRP2D_SETTINGS, kind_hint(S, "chirp2d"))
    if c is None:
        return
    RUN_LABEL        = str(c["RUN_LABEL"]).strip()
    SAMPLE           = c["SAMPLE"]
    MAS_INFO         = c["MAS_INFO"]
    REPEATS          = c["REPEATS"]
    OFF_MODE         = str(c["OFF_MODE"]).strip().lower()
    D1               = c["D1"]
    DS               = c["DS"]
    ON_SCANS         = c["ON_SCANS"]
    OFF_SCANS        = c["OFF_SCANS"]
    INTENSITY_MODE   = str(c["INTENSITY_MODE"]).strip().lower()
    SHAPE            = str(c["CHIRP_SHAPE"]).strip().upper()
    ORDER            = str(c["ORDER"]).strip().lower()
    CW_RECORD        = bool(c["CW_RECORD"])
    fail = failer(RUN_LABEL)
    h = html_text

    if not re.match(r"^[A-Za-z0-9_-]+$", RUN_LABEL):
        fail("RUN_LABEL may contain only letters, digits, '-' and '_' (got '%s')." % RUN_LABEL)
        return
    if OFF_MODE not in ("start", "end", "both", "none"):
        fail("OFF_MODE must be 'start', 'end', 'both' or 'none' (got '%s')." % OFF_MODE)
        return
    if INTENSITY_MODE not in ("extreme", "max", "sum"):
        fail("INTENSITY_MODE must be 'extreme', 'max' or 'sum' (got '%s')." % INTENSITY_MODE)
        return
    if not isinstance(REPEATS, int) or REPEATS < 1:
        fail("REPEATS must be a positive integer.")
        return
    if SHAPE not in CHIRP_SHAPES:
        fail("CHIRP_SHAPE must be one of %s (got '%s')." % (", ".join(sorted(CHIRP_SHAPES)), c["CHIRP_SHAPE"]))
        return
    if ORDER not in ("center_out", "grid"):
        fail("ORDER must be 'center_out' or 'grid' (got '%s')." % c["ORDER"])
        return
    try:
        FREQ, POWER, RATE_CENTER = float(c["FREQ"]), float(c["POWER"]), float(c["RATE_CENTER"])
    except CATCH:
        fail("FREQ (GHz), POWER (V) and RATE_CENTER (MHz/us) must be numbers.")
        return
    if not check_power(fail, "POWER", POWER):
        return
    if RATE_CENTER <= 0:
        fail("RATE_CENTER must be above 0 (got %g)." % RATE_CENTER)
        return
    grid = {}
    for name in ("WIDTHS_MHZ", "TIMES_US"):
        try:
            vals = [float(x) for x in c[name]]
        except CATCH:
            fail("%s must be a list of numbers." % name)
            return
        if not vals or [x for x in vals if not x > 0]:
            fail("%s must be a non-empty list of values above 0 (the CW record is the zero-width point)."
                 % name)
            return
        if len(set(vals)) != len(vals):
            fail("%s lists a value twice." % name)
            return
        grid[name] = sorted(vals)
    widths, times = grid["WIDTHS_MHZ"], grid["TIMES_US"]
    rate_lo, rate_hi = 0.0, float("inf")
    if c["RATE_RANGE"] is not None:
        try:
            rate_lo, rate_hi = [float(x) for x in c["RATE_RANGE"]]
        except CATCH:
            fail("RATE_RANGE must be None or (lowest, highest) sweep rate in MHz/us.")
            return
        if not 0 <= rate_lo < rate_hi:
            fail("RATE_RANGE must be (lowest, highest) with 0 <= lowest < highest (got %r)." % (c["RATE_RANGE"],))
            return
    chirps = [(w, t) for t in times for w in widths if rate_lo <= chirp_rate(w, t, SHAPE) <= rate_hi]
    if not chirps:
        fail("No chirp of the grid has a rate within RATE_RANGE %r." % (c["RATE_RANGE"],))
        return
    if ORDER == "center_out":
        chirps.sort(key=lambda p: (round(abs(math.log(chirp_rate(p[0], p[1], SHAPE) / RATE_CENTER)), 9), p[0], p[1]))
    shape_desc = "%s (%s)" % (SHAPE, CHIRP_SHAPES[SHAPE])

    # ---- Run plan: per set an optional OFF, the CW record, the chirps, an optional OFF -----
    per_set = []
    if OFF_MODE in ("start", "both"):
        per_set.append(("OFF", "start"))
    if CW_RECORD:
        per_set.append(("CW", None))
    for p in chirps:
        per_set.append(("CHIRP", p))
    if OFF_MODE in ("end", "both"):
        per_set.append(("OFF", "end"))
    records_per_set = len(per_set)
    n_on_per_set = len(chirps) + (1 if CW_RECORD else 0)
    n_off_per_set = records_per_set - n_on_per_set

    def set_tag(set_number):
        return ("set %d | " % set_number) if REPEATS > 1 else ""

    def make_plan(start_expno):
        plan = []
        for set_number in range(1, REPEATS + 1):
            base = start_expno + (set_number - 1) * records_per_set
            tag = set_tag(set_number)
            for i in range(records_per_set):
                kind, val = per_set[i]
                rec = {"expno": base + i, "set": set_number, "d1": D1, "width": None, "ctime": None}
                if kind == "OFF":
                    rec.update({
                        "kind": "OFF", "label": val, "freq": None, "ns": OFF_SCANS, "awg": "stop",
                        "title": ("OFF (%s) | %s%s | %s | microwave off | D1 = %s s | %d scans"
                                  % (val, tag, SAMPLE, MAS_INFO, D1, OFF_SCANS)),
                        "what": "%sOFF %s" % (tag, val)})
                elif kind == "CW":
                    cmdstr = 'cw %.3f %.3f' % (FREQ, POWER)
                    rec.update({
                        "kind": "ON", "label": "cw", "freq": FREQ, "ns": ON_SCANS, "awg": cmdstr, "width": 0.0,
                        "title": ("chirp grid, CW | %s%s | %s | %s | D1 = %s s | %d scan(s)"
                                  % (tag, SAMPLE, MAS_INFO, cmdstr, D1, ON_SCANS)),
                        "what": "%sCW" % tag, "skip": "%sCW" % tag, "last": "CW"})
                else:
                    w, t = val
                    cmdstr = 'chirp %.3f %g %g %s %.3f' % (FREQ, w, t, SHAPE, POWER)
                    rec.update({
                        "kind": "ON", "label": "chirp", "freq": FREQ, "ns": ON_SCANS, "awg": cmdstr,
                        "width": w, "ctime": t,
                        "title": ("chirp grid | %s%s | %s | %s | %g MHz/us | D1 = %s s | %d scan(s)"
                                  % (tag, SAMPLE, MAS_INFO, cmdstr, chirp_rate(w, t, SHAPE), D1, ON_SCANS)),
                        "what": "%schirp %g MHz, %g us" % (tag, w, t),
                        "skip": "%s%g MHz, %g us" % (tag, w, t), "last": "%g MHz, %g us" % (w, t)})
                plan.append(rec)
        return plan

    def dialog_rows(plan):
        def set_line(set_number):
            recs = [p for p in plan if p["set"] == set_number]
            parts = []
            for p in recs:
                if p["kind"] == "OFF":
                    parts.append("OFF %d" % p["expno"])
                elif p["label"] == "cw":
                    parts.append("CW %d" % p["expno"])
            ch = [p["expno"] for p in recs if p["label"] == "chirp"]
            parts.insert(len(parts) - (1 if OFF_MODE in ("end", "both") else 0), "chirps %d&#8211;%d" % (ch[0], ch[-1]))
            pre = ("set %d: " % set_number) if REPEATS > 1 else ""
            return pre + ", then ".join(parts)

        shown = list(range(1, REPEATS + 1))
        if REPEATS > 6:
            shown = [1, 2, 3, None, REPEATS]
        plan_html = "<br>".join([("..." if n is None else set_line(n)) for n in shown])
        order_of = dict((p, i + 1) for i, p in enumerate(chirps))
        cells = ["<tr><td></td>" + "".join(["<td align='center'><b>%g MHz</b></td>" % w for w in widths]) + "</tr>"]
        for t in times:
            row = "<tr><td align='right'><b>%g us</b></td>" % t
            for w in widths:
                r = chirp_rate(w, t, SHAPE)
                if (w, t) in order_of:
                    row += "<td align='center'>#%d: %.3g</td>" % (order_of[(w, t)], r)
                else:
                    row += "<td align='center'><font color='#9a9a9a'>(%.3g)</font></td>" % r
            cells.append(row + "</tr>")
        grid_html = ("%d chirps per set, in the order #; each cell: order and sweep rate (MHz/us)%s<br>"
                     "<table cellpadding='2' cellspacing='0' border='1'>%s</table>"
                     % (len(chirps), "; grey: outside RATE_RANGE, not acquired" if len(chirps) < len(widths) * len(times)
                        else "", "".join(cells)))
        return [("Plan", plan_html),
                ("mm-wave", "centre %.3f GHz, %s chirps, AWG 'chirp %.3f &lt;width&gt; &lt;time&gt; %s %.3f'%s"
                 % (FREQ, h(shape_desc), FREQ, SHAPE, POWER,
                    ("; CW record 'cw %.3f %.3f'" % (FREQ, POWER)) if CW_RECORD else "; no CW record")),
                ("Grid", grid_html),
                ("Scans", "ON records NS %d%s; D1 %s s, DS %d"
                 % (ON_SCANS, (", OFF records NS %d" % OFF_SCANS) if n_off_per_set else "", h(D1), DS))]

    def timing(plan, record_time):
        per_point_time = record_time(ON_SCANS, D1)
        off_time       = record_time(OFF_SCANS, D1)
        total_time     = REPEATS * (per_point_time * n_on_per_set + off_time * n_off_per_set)
        note = ("ON ~%s per record, OFF ~%s each" % (fmt_dur(per_point_time), fmt_dur(off_time))
                if n_off_per_set else "~%s per record" % fmt_dur(per_point_time))
        return total_time, note

    def header(run_id, ds_root, peak_str, started):
        return ("# fs run file (read by dnp_viewer.py and fs_rephase.py)\n"
                "# type = chirp2d\n"
                "# run_id = %s\n"
                "# label = %s\n"
                "# sample = %s\n"
                "# conditions = %s\n"
                "# dataset_dir = %s\n"
                "# off_mode = %s\n"
                "# peak_ppm = %s\n"
                "# window_ppm = %s\n"
                "# mode = %s\n"
                "# freq_GHz = %.4f\n"
                "# power = %.3f\n"
                "# shape = %s\n"
                "# grid_widths_MHz = %s\n"
                "# grid_times_us = %s\n"
                "# order = %s\n"
                "# rate_center = %g\n"
                "# chirps = %s\n"
                "# d1 = %s\n"
                "# repeats = %d\n"
                "# started = %s\n"
                "# width_MHz, time_us: of the chirp; the CW record has width 0\n"
                "# columns: expno, kind, label, freq_GHz, ns, finished, set, width_MHz, time_us\n"
                % (run_id, RUN_LABEL, SAMPLE, MAS_INFO, ds_root, OFF_MODE, peak_str,
                   repr(float(c["PEAK_WINDOW_PPM"])), INTENSITY_MODE, FREQ, POWER, SHAPE,
                   ",".join(["%g" % w for w in widths]), ",".join(["%g" % t for t in times]),
                   ORDER, RATE_CENTER, ",".join(["%gx%g" % p for p in chirps]), D1, REPEATS, started))

    def row_extra(rec):
        if rec["kind"] != "ON":
            return "\t-\t-"
        if rec["label"] == "cw":
            return "\t0\t-"
        return "\t%g\t%g" % (rec["width"], rec["ctime"])

    run_records(c, {
        "noun": "chirp grid", "kind": "chirp2d", "table": CHIRP2D_SETTINGS, "make_plan": make_plan,
        "dialog_rows": dialog_rows, "timing": timing, "header": header,
        "used": {"OFF_MODE": OFF_MODE, "FREQ": FREQ, "POWER": POWER, "CHIRP_SHAPE": SHAPE, "ORDER": ORDER,
                 "WIDTHS_MHZ": widths, "TIMES_US": times},
        "settings_comments": lambda plan, record_time: [],
        "row_extra": row_extra,
        "d1_column": False, "on_noun": "ON records",
        "start_desc": "%d set(s), OFF mode %s, %d chirps per set at %.3f GHz (%s)%s"
                      % (REPEATS, OFF_MODE, len(chirps), FREQ, shape_desc, ", with a CW record" if CW_RECORD else ""),
        "end_desc": "%d set(s), OFF mode %s" % (REPEATS, OFF_MODE)}, source)


def acqus_values(path):
    """{name: value} from a JCAMP acqus file: '##$NAME= value', and for arrays
    ('##$D= (0..63)' followed by the values) a list of strings."""
    out = {}
    fh = open(path, "r")
    try:
        lines = fh.read().split("\n")
    finally:
        fh.close()
    i = 0
    while i < len(lines):
        m = re.match(r"##\$(\w+)=\s*(.*)$", lines[i])
        if m:
            key, val = m.group(1), m.group(2).strip()
            if re.match(r"^\(\d+\.\.\d+\)$", val):
                vals = []
                i += 1
                while i < len(lines) and not lines[i].startswith("##"):
                    vals += lines[i].split()
                    i += 1
                out[key] = vals
                continue
            out[key] = val.strip("<>")
        i += 1
    return out


def acq_file_values(folder, prefer):
    """acqus_values() of folder/prefer ('acqu' or 'acqus'), else of the other file; {} if
    neither can be read. acqu holds an expno's current parameters (what wrpa copies and zg
    uses), acqus those of its last acquisition."""
    other = "acqus" if prefer == "acqu" else "acqu"
    for name in (prefer, other):
        try:
            return acqus_values(os.path.join(folder, name))
        except CATCH:
            pass
    return {}


def acq_number(acq, key, index=None):
    """A number from acqus_values(); None if missing."""
    try:
        v = acq[key]
        if index is not None:
            v = v[index]
        return float(v)
    except CATCH:
        return None


def off_ref_check(off_ref, ds_root, template_dir, d1):
    """(expno folder, [warnings], description) of OFF_REF (an expno of ds_root, or the path
    of an expno folder); raises ValueError if it cannot be used. The warnings list the
    acquisition parameters that differ from the template's, and a D1 that differs from d1
    (from the template's if d1 is None)."""
    ref = str(off_ref).strip()
    path = os.path.join(ds_root, ref) if re.match(r"^\d+$", ref) else os.path.normpath(ref)
    if not re.match(r"^\d+$", os.path.basename(path)) or not os.path.isdir(path):
        raise ValueError("%s is not an expno folder" % path)
    if not os.path.exists(os.path.join(path, "pdata", "1", "1r")):
        raise ValueError("%s has no processed spectrum (pdata/1/1r); process it first" % path)
    try:
        ra = acqus_values(os.path.join(path, "acqus"))        # what the reference was acquired with
    except CATCH as ex:
        raise ValueError("the acqus of %s could not be read (%s)" % (path, ex))
    ru = acq_file_values(path, "acqu")
    ta = acq_file_values(template_dir, "acqu")   # what the new records get (the template's acqus is
    warn = []                                    # its last acquisition, possibly with older settings)

    def differ(x, y):
        return abs(x - y) > 1e-6 * max(abs(x), abs(y), 1e-12)
    for key, idx, name, unit in (("RG", None, "RG", ""), ("D", 1, "D1", " s"), ("P", 1, "P1", " us"),
                                 ("PLW", 1, "PLW1", " W")):
        rv, tv = acq_number(ra, key, idx), acq_number(ta, key, idx)
        own = key == "D" and d1 is not None
        if own:
            tv = d1                              # the D1 this run sets, not the template's
        if rv is not None and tv is not None and differ(rv, tv):
            uv = acq_number(ru, key, idx)
            note = "" if uv is None or not differ(uv, rv) else \
                " (its acqus; its acqu has %g%s)" % (uv, unit)
            warn.append("%s %g%s in the reference%s, %g%s %s" % (name, rv, unit, note, tv, unit,
                                                                 "set for this run" if own else "in the template"))
    if ra.get("PULPROG") and ta.get("PULPROG") and ra["PULPROG"] != ta["PULPROG"]:
        warn.append("pulse program %s in the reference, %s in the template" % (ra["PULPROG"], ta["PULPROG"]))
    desc = "expno %s of %s: %s, NS %s, RG %s, D1 %s s" % (
        os.path.basename(path), os.path.dirname(path), ra.get("PULPROG", "?"), ra.get("NS", "?"),
        ra.get("RG", "?"), ("%g" % acq_number(ra, "D", 1)) if acq_number(ra, "D", 1) is not None else "?")
    return path, warn, desc


def run_records(c, job, source):
    """Acquires the records that job["make_plan"] lists, with the common settings in c
    (see run_profile and run_buildup for job). Each record is made from the template
    with wrpa, D1, NS and DS; before it, 'stop' (OFF) or its 'cw' command (ON) is sent
    to the AWG."""
    RUN_LABEL        = str(c["RUN_LABEL"]).strip()
    SAMPLE           = c["SAMPLE"]
    MAS_INFO         = c["MAS_INFO"]
    DATA_DIR         = c["DATA_DIR"]
    DATA_NAME        = c["DATA_NAME"]
    START_EXPNO      = c["START_EXPNO"]
    TEMPLATE_EXPNO   = c["TEMPLATE_EXPNO"]
    DS               = c["DS"]
    AWG_SETTLE       = c["AWG_SETTLE"]
    SCAN_OVERHEAD    = c["SCAN_OVERHEAD"]
    POLL_INTERVAL    = c["POLL_INTERVAL"]
    MAX_EXTRA_WAIT   = c["MAX_EXTRA_WAIT"]
    POST_ACQ_PAD     = c["POST_ACQ_PAD"]
    EST_OVERHEAD     = c["EST_OVERHEAD"]
    AWG_RETRIES      = c["AWG_RETRIES"]
    MAX_CONSEC_SKIPS = c["MAX_CONSEC_SKIPS"]
    PROCESS_CMDS     = list(c["PROCESS_CMDS"])
    PEAK_PPM         = c["PEAK_PPM"]
    PEAK_WINDOW_PPM  = c["PEAK_WINDOW_PPM"]
    INTENSITY_MODE   = str(c["INTENSITY_MODE"]).strip().lower()
    LAUNCH_VIEWER    = c["LAUNCH_VIEWER"]
    RESPAWN_VIEWER   = c["RESPAWN_VIEWER"]
    fail = failer(RUN_LABEL)

    # ---- Dataset and template: from the script, or else from TopSpin ----------
    def topspin_current():
        """((dir, name, expno), '') of the dataset open in TopSpin, or (None, reason)."""
        try:
            cd = CURDATA()                       # [NAME, EXPNO, PROCNO, DIR]
        except CATCH as ex:
            return None, "the dataset open in TopSpin could not be read (%s)" % ex
        if cd is None or len(cd) < 4:
            return None, "no dataset is open in TopSpin"
        try:
            return (str(cd[3]), str(cd[0]), int(str(cd[1]))), ""
        except CATCH as ex:
            return None, "TopSpin returned an unexpected dataset %s (%s)" % (cd, ex)

    src_name = os.path.basename(source) if source else "the script"
    ds_from = "set in %s" % src_name
    if DATA_DIR and DATA_NAME:
        pass
    elif not DATA_DIR and not DATA_NAME:
        cur, why = topspin_current()
        if cur is None:
            fail("DATA_DIR and DATA_NAME are empty, so the dataset open in TopSpin would be used, "
                 "but %s." % why)
            return
        DATA_DIR, DATA_NAME = cur[0], cur[1]
        ds_from = "taken from TopSpin: the dataset open when the script started"
    else:
        fail("set both DATA_DIR and DATA_NAME, or leave both empty to use the dataset open in TopSpin.")
        return
    DATA_DIR, DATA_NAME = str(DATA_DIR), str(DATA_NAME)
    ds_root = os.path.join(DATA_DIR, DATA_NAME)
    if not os.path.isdir(ds_root):
        fail("the dataset folder %s does not exist." % ds_root)
        return

    tmpl_from = "set in %s" % src_name
    if TEMPLATE_EXPNO is None or TEMPLATE_EXPNO == "":
        cur, why = topspin_current()
        if cur is None:
            fail("TEMPLATE_EXPNO is empty, so the expno open in TopSpin would be the template, "
                 "but %s." % why)
            return
        if os.path.normpath(os.path.join(cur[0], cur[1])) != os.path.normpath(ds_root):
            fail("TEMPLATE_EXPNO is empty, so the expno open in TopSpin would be the template, but "
                 "TopSpin shows %s (expno %d), not this run's dataset %s.\nOpen the template expno "
                 "of %s in TopSpin, or set TEMPLATE_EXPNO."
                 % (os.path.join(cur[0], cur[1]), cur[2], ds_root, ds_root))
            return
        TEMPLATE_EXPNO = cur[2]
        tmpl_from = "taken from TopSpin: the expno open when the script started"
    try:
        TEMPLATE_EXPNO, START_EXPNO = int(TEMPLATE_EXPNO), int(START_EXPNO)
    except CATCH:
        fail("TEMPLATE_EXPNO and START_EXPNO must be expno numbers.")
        return
    if not os.path.isdir(os.path.join(ds_root, str(TEMPLATE_EXPNO))):
        fail("the template expno %s/%d does not exist." % (ds_root, TEMPLATE_EXPNO))
        return

    def acqus_param(expno, key, name="acqus"):
        try:
            fh = open(os.path.join(ds_root, str(expno), name), "r")
            try:
                txt = fh.read()
            finally:
                fh.close()
            m = re.search(r"^##\$%s=\s*(.*)$" % key, txt, re.M)
            if m:
                return m.group(1).strip().strip("<>")
        except CATCH:
            pass
        return ""
    tmpl_pulprog = acqus_param(TEMPLATE_EXPNO, "PULPROG", "acqu") or acqus_param(TEMPLATE_EXPNO, "PULPROG")

    # ---- OFF reference from an earlier run (OFF_REF) ---------------------------------
    off_ref_path, off_ref_rows, off_ref_warn = None, [], []
    if c.get("OFF_REF") not in (None, ""):
        try:
            d1_run = float(c["D1"]) if c.get("D1") is not None else None
        except CATCH:
            d1_run = None
        try:
            off_ref_path, off_ref_warn, ref_desc = off_ref_check(
                c["OFF_REF"], ds_root, os.path.join(ds_root, str(TEMPLATE_EXPNO)), d1_run)
        except ValueError as ex:
            fail("OFF_REF cannot be used: %s." % ex)
            return
        txt = html_text(ref_desc) + "<br>used for I_on/I_off instead of a start OFF"
        if off_ref_warn:
            txt += "".join(["<br><font color='#b03a2e'><b>differs:</b> %s</font>" % html_text(w)
                            for w in off_ref_warn])
        off_ref_rows = [("OFF reference", txt)]

    # ---- Run plan: one dict per record, in acquisition order ---------------------
    plan = job["make_plan"](START_EXPNO)
    planned_last = plan[-1]["expno"]

    n_records = len(plan)

    def taken(first):
        return [x for x in range(first, first + n_records)
                if os.path.exists(os.path.join(ds_root, str(x)))]

    def next_free(first):
        s = first
        while s < first + 100000:
            t = taken(s)
            if not t:
                return s
            s = max(t) + 1
        return None

    def expno_list(xs):
        if len(xs) <= 6:
            return ", ".join([str(x) for x in xs])
        return ", ".join([str(x) for x in xs[:5]]) + ", ... %d" % xs[-1]

    existing = taken(START_EXPNO)
    if existing:
        fail("%d of the %d planned expnos %d..%d already exist in %s (%s).\n"
             "The first START_EXPNO with %d free expnos after it is %s."
             % (len(existing), n_records, START_EXPNO, planned_last, ds_root,
                expno_list(existing), n_records, next_free(START_EXPNO)))
        return

    # ---- Helpers ---------------------------------------------------------------
    paths = {"log": None}

    def fmt_hms(total_seconds):
        total_seconds = int(round(total_seconds))
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return "%dh %02dm %02ds" % (h, m, s)

    def now_str(t=None):
        if t is None:
            t = time.time()
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

    def log(msg):
        line = "[%s] %s" % (now_str(), msg)
        print(line)
        if paths["log"] is None:
            return
        try:
            fh = open(paths["log"], 'a')
            try:
                fh.write(line + "\n")
            finally:
                fh.close()
        except CATCH:
            pass

    def confirm_dialog(message, title):
        try:
            from javax.swing import JOptionPane
            choice = JOptionPane.showConfirmDialog(
                None, message, title,
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE)
            return choice == JOptionPane.OK_OPTION
        except CATCH as ex:
            ERRMSG("Could not display confirmation dialog: %s" % ex)
            return False

    def record_time(ns, d1):
        return AWG_SETTLE + EST_OVERHEAD + (ns + DS) * (d1 + SCAN_OVERHEAD) + POST_ACQ_PAD

    total_time, time_note = job["timing"](plan, record_time)

    # ---- Confirmation --------------------------------------------------------
    h = html_text

    if PEAK_PPM is None:
        window_desc = "whole spectrum"
        peak_str = "none"
    else:
        window_desc = "window %.1f +/- %.1f ppm" % (PEAK_PPM, PEAK_WINDOW_PPM / 2.0)
        peak_str = repr(float(PEAK_PPM))
    if not LAUNCH_VIEWER:
        viewer_desc = "not started automatically (command in the log)"
    elif RESPAWN_VIEWER:
        viewer_desc = "opens automatically, and again after a record if closed"
    else:
        viewer_desc = "opens automatically"


    t_end = time.time() + total_time
    if time.strftime("%Y%m%d", time.localtime(t_end)) == time.strftime("%Y%m%d"):
        end_str = time.strftime("%H:%M", time.localtime(t_end))
    else:
        end_str = time.strftime("%a %H:%M", time.localtime(t_end))
    grey = "<font color='#5a5a5a'>%s</font>"
    big = "<span style='font-size:17pt'><b>%s</b></span>"
    summary = (
        "<html><body style='width:640px'>"
        "<p><span style='font-size:14pt'><b>Start the '%s' %s?</b></span></p>"
        "<table cellpadding='5' cellspacing='0' bgcolor='#e8eef8' width='100%%'>"
        "<tr><td valign='top' width='100' nowrap>Dataset</td><td>%s<br>%s</td></tr>"
        "<tr><td valign='top' width='100' nowrap>New expnos</td><td>%s<br>%s</td></tr>"
        "<tr><td valign='top' width='100' nowrap>Template</td><td>%s<br>%s</td></tr>"
        "</table>"
        "<table cellpadding='3' cellspacing='0'>"
        "<tr><td valign='top' width='100' nowrap><b>Sample</b></td><td>%s<br>%s</td></tr>"
        % (h(RUN_LABEL), job["noun"],
           big % h(ds_root), grey % h(ds_from),
           big % ("%d &#8211; %d" % (START_EXPNO, planned_last)),
           grey % ("%d records, none of them exists yet" % n_records),
           big % ("expno %d" % TEMPLATE_EXPNO) + ("&nbsp;&nbsp;%s" % h(tmpl_pulprog) if tmpl_pulprog else ""),
           grey % h(tmpl_from),
           h(SAMPLE), grey % h(MAS_INFO))
        + "".join(["<tr><td valign='top'><b>%s</b></td><td>%s</td></tr>" % (k, v)
                   for k, v in job["dialog_rows"](plan) + off_ref_rows])
        + "<tr><td valign='top'><b>Time</b></td><td><b>about %s</b>, ending around %s<br>%s</td></tr>"
        "<tr><td valign='top'><b>Records</b></td><td>%s</td></tr>"
        "<tr><td valign='top'><b>Live plot</b></td><td>%s, %s; the viewer %s</td></tr>"
        "</table>"
        "<p style='margin-top:8px'>%s</p>"
        "<p style='margin-top:10px'><span style='font-size:13pt'><b>OK</b> starts the run. "
        "<b>Cancel</b> creates nothing.</span></p>"
        "</body></html>"
        % (fmt_dur(total_time), end_str, grey % time_note,
           h(os.path.join(ds_root, RUNS_SUBDIR, "%s_%s_<start time>_e%d" % (RUN_LABEL, job["kind"], START_EXPNO))),
           h(window_desc), h(INTENSITY_MODE), viewer_desc,
           grey % ("Timing: scan ~ D1 + %s s; poll every %s s; stop if a record runs %s s past its "
                   "expected end; %s s pad before each AWG change." % (SCAN_OVERHEAD, POLL_INTERVAL,
                                                                     MAX_EXTRA_WAIT, POST_ACQ_PAD)))
    )
    if SETTINGS_NOTES:
        summary = summary.replace(
            "<p style='margin-top:10px'>",
            "".join(["<p style='margin-top:6px;color:#a04000'>Note: %s</p>" % h(n) for n in SETTINGS_NOTES])
            + "<p style='margin-top:10px'>", 1)
    if not confirm_dialog(summary, "Confirm '%s' run" % RUN_LABEL):
        MSG("%s: run cancelled by user before start." % RUN_LABEL)
        return
    existing = taken(START_EXPNO)
    if existing:
        ERRMSG("%s: expno(s) %s of the planned %d..%d appeared after the dialog was shown. "
               "Nothing was started." % (RUN_LABEL, expno_list(existing), START_EXPNO, planned_last))
        return

    # ---- Run folder ------------------------------------------------------------
    run_id  = "%s_%s_%s_e%d" % (RUN_LABEL, job["kind"], time.strftime("%Y%m%d-%H%M%S"), START_EXPNO)
    run_dir = os.path.join(ds_root, RUNS_SUBDIR, run_id)
    try:
        os.makedirs(run_dir)
    except CATCH as ex:
        ERRMSG("%s: could not create the run folder %s (%s). Nothing was started."
               % (RUN_LABEL, run_dir, ex))
        return
    RUN_PATH   = os.path.join(run_dir, "run.txt")
    VIEWER_LOG = os.path.join(run_dir, "viewer.log")
    paths["log"] = os.path.join(run_dir, "log.txt")
    used = dict(c)
    used.update(job["used"])
    used.update(RUN_LABEL=RUN_LABEL, DATA_DIR=DATA_DIR, DATA_NAME=DATA_NAME,
                TEMPLATE_EXPNO=TEMPLATE_EXPNO, START_EXPNO=START_EXPNO,
                INTENSITY_MODE=INTENSITY_MODE, PROCESS_CMDS=PROCESS_CMDS)
    try:
        fh = open(os.path.join(run_dir, "settings.txt"), "w")
        try:
            fh.write("# settings of run %s, as used (written by dnp_core.py)\n" % run_id)
            fh.write("# dataset: %s, %s\n" % (ds_root, ds_from))
            fh.write("# template: expno %d (%s), %s\n" % (TEMPLATE_EXPNO, tmpl_pulprog or "?", tmpl_from))
            fh.write("# expnos: %d..%d\n" % (START_EXPNO, planned_last))
            fh.write("# settings file: %s\n" % (source or "-"))
            for line in job["settings_comments"](plan, record_time):
                fh.write(line + "\n")
            for n, d in job["table"]:
                fh.write("%s = %r\n" % (n, used[n]))
        finally:
            fh.close()
    except CATCH as ex:
        print("could not write settings.txt [%s]" % ex)
    if source:
        try:
            import shutil
            shutil.copyfile(source, os.path.join(run_dir, os.path.basename(source)))
        except CATCH as ex:
            print("could not copy %s into the run folder [%s]" % (source, ex))
    viewer_cmd = "%s %s %s" % (VIEWER_PYTHON, VIEWER_PATH, RUN_PATH)

    def run_file_write(text, mode='a'):
        """Write to run.txt. A failure is logged but does not stop the run."""
        try:
            fh = open(RUN_PATH, mode)
            try:
                fh.write(text)
            finally:
                fh.close()
        except CATCH as ex:
            log("Could not write run file %s [%s]" % (RUN_PATH, ex))

    def run_file_header():
        text = job["header"](run_id, ds_root, peak_str, now_str())
        text = text.replace("# columns:", "# code_version = %s\n# columns:" % code_version(), 1)
        if off_ref_path:
            text = text.replace("# columns:", "# off_ref = %s\n# columns:" % off_ref_path, 1)
        run_file_write(text, 'w')

    def run_file_row(rec, t_fin):
        if rec["freq"] is None:
            fstr = "-"
        else:
            fstr = "%.4f" % rec["freq"]
        line = ("%d\t%s\t%s\t%s\t%d\t%s\t%d"
                % (rec["expno"], rec["kind"], rec["label"], fstr, rec["ns"], now_str(t_fin), rec["set"]))
        if job["d1_column"]:
            line += "\t%s" % rec["d1"]
        if job.get("row_extra"):
            line += job["row_extra"](rec)
        run_file_write(line + "\n")

    def clean(x):
        return str(x).replace("\t", " ").replace("\n", " ")

    def index_event(event, status):
        """One line in the common index. A failure is logged but does not stop the run."""
        user = os.environ.get("USER") or os.environ.get("LOGNAME") or "?"
        line = "\t".join([now_str(), event, clean(status), run_id, RUN_LABEL, clean(SAMPLE),
                          ds_root, "%d-%d" % (START_EXPNO, planned_last), run_dir, user,
                          job["kind"]])
        try:
            new = (not os.path.exists(INDEX_PATH)) or os.path.getsize(INDEX_PATH) == 0
            fh = open(INDEX_PATH, 'a')
            try:
                if new:
                    fh.write("# time\tevent\tstatus\trun_id\tlabel\tsample\tdataset\texpnos"
                             "\trun_folder\tuser\ttype\n")
                fh.write(line + "\n")
            finally:
                fh.close()
        except CATCH as ex:
            log("Could not write to the run index %s [%s]" % (INDEX_PATH, ex))

    def re_abs(expno):
        XCMD("re %s %d 1 %s" % (DATA_NAME, expno, DATA_DIR),
             wait=WAIT_TILL_DONE)

    def set_title(expno, title):
        try:
            path = os.path.join(ds_root, str(expno), 'pdata', '1', 'title')
            tdir = os.path.dirname(path)
            if not os.path.exists(tdir):
                os.makedirs(tdir)
            fh = open(path, 'w')
            try:
                fh.write(title)
            finally:
                fh.close()
        except CATCH:
            pass

    def new_record(expno, ns, d1, title):
        re_abs(TEMPLATE_EXPNO)
        XCMD("wrpa " + str(expno), wait=WAIT_TILL_DONE)
        re_abs(expno)
        XCMD("d1 " + str(d1))
        XCMD("ns " + str(ns))
        XCMD("ds " + str(DS))
        set_title(expno, title)

    def awg(cmdstr):
        """Send a command to the AWG, with retries. Returns True on success."""
        for attempt in range(1, AWG_RETRIES + 1):
            log("AWG -> '%s'%s" % (cmdstr, "" if attempt == 1 else "  (attempt %d)" % attempt))
            try:
                subprocess.check_call([AWG_PYTHON, AWG_CMD_PATH, cmdstr])
                return True
            except CATCH as ex:
                log("AWG command failed: '%s'  [%s]" % (cmdstr, ex))
                if attempt < AWG_RETRIES:
                    SLEEP(5)
        return False

    def audita_time(expno, threshold):
        """mtime of the expno's audita.txt if it is later than threshold, else None."""
        p = os.path.join(ds_root, str(expno), 'audita.txt')
        try:
            if os.path.exists(p):
                m = os.path.getmtime(p)
                if m > threshold:
                    return m
        except CATCH:
            pass
        return None

    def process(expno):
        """Run PROCESS_CMDS on the finished record. A failure is logged but does
        not stop the run."""
        if not PROCESS_CMDS:
            return
        try:
            re_abs(expno)
            for cmd in PROCESS_CMDS:
                XCMD(cmd, wait=WAIT_TILL_DONE)
            log("expno %d: processed (%s)" % (expno, "; ".join(PROCESS_CMDS)))
        except CATCH as ex:
            log("expno %d: processing failed (%s)  [%s]" % (expno, "; ".join(PROCESS_CMDS), ex))

    def acquire(expno, ns, d1, label):
        """Start zg and return only once the acquisition has finished.
        Raises RunAbort if it has not finished MAX_EXTRA_WAIT s past the expected end."""
        lower    = (ns + DS) * d1                       # hard lower bound on the duration
        expected = (ns + DS) * (d1 + SCAN_OVERHEAD)
        t_zg = time.time()
        log("expno %d: zg  [%s, NS=%d, DS=%d, D1=%s s, expected ~%d s]"
            % (expno, label, ns, DS, d1, expected))
        XCMD("zg", wait=WAIT_TILL_DONE)
        t_ret = time.time()
        if t_zg + lower > t_ret:
            SLEEP(int(t_zg + lower - t_ret + 0.999))
        threshold = t_zg + lower
        deadline  = t_zg + expected + MAX_EXTRA_WAIT
        while True:
            t_fin = audita_time(expno, threshold)
            if t_fin is not None:
                log("expno %d: finished %d s after zg (expected ~%d s; zg returned after %d s)"
                    % (expno, int(round(t_fin - t_zg)), expected, int(round(t_ret - t_zg))))
                process(expno)
                if POST_ACQ_PAD > 0:
                    SLEEP(POST_ACQ_PAD)
                return t_fin
            if time.time() >= deadline:
                raise RunAbort(
                    "expno %d (%s) had not finished %d s after zg (expected ~%d s). "
                    "The acquisition itself was not halted; check its status in TopSpin"
                    % (expno, label, int(round(time.time() - t_zg)), expected))
            SLEEP(POLL_INTERVAL)

    def run_record(rec):
        """Sets the AWG and acquires the record. Returns the finish time, or None if the
        'cw' command of an ON record could not be sent (record skipped, expno left
        empty); a failed 'stop' before an OFF record stops the run."""
        if rec["kind"] == "OFF":
            if not awg('stop'):
                raise RunAbort("could not send 'stop' to the AWG before the %s (expno %d)"
                               % (rec["what"], rec["expno"]))
        elif not awg(rec["awg"]):
            return None
        SLEEP(AWG_SETTLE)
        new_record(rec["expno"], rec["ns"], rec["d1"], rec["title"])
        return acquire(rec["expno"], rec["ns"], rec["d1"], rec["what"])
    # ---- Viewer -------------------------------------------------------------------
    def launch_viewer():
        """Start dnp_viewer.py detached from TopSpin, with the Python variables of
        TopSpin's Jython removed from its environment. Output goes to viewer.log.
        Returns True if the start command was issued, False otherwise."""
        def q(x):
            return "'" + str(x).replace("'", "'\\''") + "'"
        shell_cmd = ("nohup env -u PYTHONPATH -u PYTHONHOME %s %s %s >> %s 2>&1 &"
                     % (q(VIEWER_PYTHON), q(VIEWER_PATH), q(RUN_PATH), q(VIEWER_LOG)))
        try:
            if not os.path.exists(VIEWER_PATH):
                raise IOError("%s not found" % VIEWER_PATH)
            subprocess.Popen(['/bin/sh', '-c', shell_cmd])
            log("Viewer started (output in %s)" % VIEWER_LOG)
            return True
        except CATCH as ex:
            log("Viewer could not be started [%s]" % ex)
            return False

    def ere_escape(s):
        """s as a literal string in a POSIX extended regular expression (for pgrep)."""
        special = '.[]()*+?{}|^$\\'
        return "".join([("\\" + ch) if ch in special else ch for ch in s])

    # A viewer for this run is any process whose command line contains the file
    # name of dnp_viewer.py followed by <run id>/run.txt; this also matches a viewer
    # opened by hand with an absolute path or a path relative to the dataset.
    viewer_pattern = (ere_escape(os.path.basename(VIEWER_PATH)) + ".*"
                      + ere_escape(run_id + "/run.txt"))
    viewer_state = {"respawn": bool(LAUNCH_VIEWER and RESPAWN_VIEWER)}

    def viewer_running():
        """True if a viewer for this run is running, False if none is,
        None if pgrep could not be run or reported an error."""
        try:
            p = subprocess.Popen(['pgrep', '-f', viewer_pattern],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
        except CATCH as ex:
            log("Could not check whether the viewer is running [%s]" % ex)
            return None
        if p.returncode == 0:
            return True
        if p.returncode == 1:
            return False
        log("Could not check whether the viewer is running [pgrep exit status %s]"
            % p.returncode)
        return None

    def respawn_viewer(expno):
        """Called after a record has been added to run.txt: start the viewer
        again if none is running. A failure is logged and ends the restarts for
        the rest of the run; it does not stop the run."""
        if not viewer_state["respawn"]:
            return
        try:
            running = viewer_running()
            if running is None:
                viewer_state["respawn"] = False
            elif not running:
                log("No viewer running after expno %d; starting it again" % expno)
                if not launch_viewer():
                    viewer_state["respawn"] = False
            if not viewer_state["respawn"]:
                log("The viewer will not be restarted during this run; reopen it with: %s"
                    % viewer_cmd)
        except CATCH as ex:
            viewer_state["respawn"] = False
            log("Viewer check failed [%s]; the viewer will not be restarted during this run"
                % ex)

    # ---- Main loop over the plan -------------------------------------------------
    log("=== %s start: %s / %s, %s, expno %d..%d, estimated %s ==="
        % (RUN_LABEL, DATA_NAME, DATA_DIR, job["start_desc"], START_EXPNO, planned_last,
           fmt_hms(total_time)))
    log("Run folder: %s" % run_dir)
    if off_ref_path:
        log("OFF reference: %s%s" % (off_ref_path, "".join(["; differs: " + w for w in off_ref_warn])))
    run_file_header()
    index_event("start", "running")
    log("Viewer command: %s" % viewer_cmd)
    if LAUNCH_VIEWER:
        running = viewer_running()
        if running:
            log("A viewer for this run is already running; not starting another")
        else:
            if running is None:
                viewer_state["respawn"] = False
                log("The viewer will not be restarted during this run; reopen it with: %s"
                    % viewer_cmd)
            if not launch_viewer():
                viewer_state["respawn"] = False

    n_on_done = 0
    n_off_done = 0
    last_expno = None
    skipped = []
    consec_skips = 0
    abort_reason = None
    stop_ok = False
    plan_done = False

    try:
        ops = {"awg": awg, "new_record": new_record, "acquire": acquire, "log": log,
               "acqus_param": acqus_param}
        for rec in plan:
            expno = rec["expno"]
            if job.get("record_runner"):          # decay: its own AWG and D1 timing
                t_fin = job["record_runner"](rec, ops)
            else:
                t_fin = run_record(rec)
            if rec["kind"] == "OFF":
                run_file_row(rec, t_fin)
                respawn_viewer(expno)
                n_off_done += 1
                last_expno = expno
            elif t_fin is not None:
                run_file_row(rec, t_fin)
                respawn_viewer(expno)
                n_on_done += 1
                last_expno = expno
                consec_skips = 0
            else:
                skipped.append((rec["set"], rec["freq"], expno))
                consec_skips += 1
                log("Skipped %s (expno %d left empty)" % (rec["skip"], expno))
                if consec_skips >= MAX_CONSEC_SKIPS:
                    raise RunAbort("%d %s in a row could not be set on the AWG "
                                   "(last: %s)" % (consec_skips, job["on_noun"], rec["last"]))
        plan_done = True
    except RunAbort as ex:
        abort_reason = str(ex)
    except CATCH as ex:
        abort_reason = "unexpected error: %s" % ex
    finally:
        # Also reached if the script is stopped from TopSpin, as far as the
        # interrupt allows; then neither handler above runs and plan_done is False.
        if abort_reason:
            log("STOPPED: %s" % abort_reason)
            status = "stopped: %s" % abort_reason.replace("\n", " ")
        elif plan_done:
            status = "complete"
        else:
            log("STOPPED: interrupted before the end of the plan (script stopped from TopSpin?)")
            status = "stopped: interrupted before the end of the plan"
        stop_ok = awg('stop')
        run_file_write("# end: %s\n" % status)
        index_event("end", status)
        if not abort_reason and not plan_done:
            log("=== interrupted; final 'stop' %s ===" % ("sent" if stop_ok else "FAILED"))

    done = ("%d ON and %d OFF records acquired, last at expno %s"
            % (n_on_done, n_off_done, last_expno))
    if skipped:
        done += "; skipped %d point(s), expno %s left empty" % (
            len(skipped), ", ".join([str(s[2]) for s in skipped]))
    log("=== %s end: %s; final 'stop' %s ===" % (RUN_LABEL, done, "sent" if stop_ok else "FAILED"))

    if abort_reason:
        ERRMSG("%s STOPPED: %s.\n\nmm-wave 'stop' %s.\nCompleted: %s.\nRun folder: %s"
               % (RUN_LABEL, abort_reason,
                  "sent" if stop_ok else "COULD NOT BE SENT - CHECK THE SOURCE",
                  done, run_dir))
    elif not stop_ok:
        ERRMSG("%s finished, but the final 'stop' could not be sent - CHECK THE SOURCE.\n"
               "%s.\nRun folder: %s" % (RUN_LABEL, done, run_dir))
    else:
        MSG("%s complete: %s. %s. 'stop' sent to AWG.\nRun folder: %s\n"
            "Plot: %s" % (RUN_LABEL, job["end_desc"], done, run_dir, viewer_cmd))
