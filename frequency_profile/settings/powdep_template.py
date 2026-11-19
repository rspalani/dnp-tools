# powdep_template.py  -  template for the settings files of powdep.py (DNP enhancement
# against mm-wave power)
#
# To set up a new kind of power dependence, copy this file in the same folder:
#     cp /opt/nmrdata/fs_settings/powdep_template.py /opt/nmrdata/fs_settings/powdep_<name>.py
# fill in the values, and run it from TopSpin's command line with
#     powdep <name>
# ('powdep' alone lists the power-dependence settings files to choose from). This
# template itself is not run.
#
# A power-dependence run is a frequency profile at one frequency, FREQ, in which the
# AWG drive voltage (the second argument of the AWG 'cw' command) changes from record to
# record. Each set is an optional OFF record, one ON record per voltage, and an
# optional OFF record (OFF_MODE, as for profiles); the viewer plots I_on/I_off - 1
# against the power, with the start OFF of the set as the reference.
#
# The voltages are given either directly, as VOLTAGES (V), or as POWER_FRACTIONS:
# fractions of the power at full drive (0.4 V), converted to voltages with the
# source's calibration, /opt/dnptools/awg_power_cal.txt (drive voltage against output
# power, measured at 526.012 GHz; the ratio to full power is taken to hold at every
# frequency). The source saturates near full drive (about 97% of full power at 0.35 V),
# so evenly spaced voltages put most points at the top of the power axis;
# POWER_FRACTIONS spaces them in power instead. Nothing above 0.4 V is sent, and
# voltages below the lowest calibration point (0.1 V, about 9% of full power) are
# refused, since their power is not known; add calibration points to go lower.
#
# D1: T_B shortens as the power rises. For the steady-state enhancement at every power,
# D1 must be several T_B at the lowest power; a shorter D1 gives an enhancement that
# also depends on the build-up rate at each power.
#
# The file is Python: plain assignments, with frange(start, stop, step) and
# logspace(first, last, n) available. UPPERCASE names are settings; an UPPERCASE
# name that is not a known setting stops the run before anything starts. Settings
# left out take the defaults in /opt/dnptools/fs_core.py (POWDEP_SETTINGS).
#
# Each run is recorded as a frequency profile is, in
# <dataset>/fs_runs/<start time>_<RUN_LABEL>_e<START_EXPNO>/, and listed in
# /opt/nmrdata/fs_runs.tsv.

# Short name used in the run folder name and the index. Leave it out to use
# powdep_<name> from the file name powdep_<name>.py.
#RUN_LABEL = "powdep_name"

SAMPLE   = "sample description"          # shown in the dialog, the titles and the plot
MAS_INFO = "MAS rate, rotor, temperature"

# Dataset and template expno, as for profiles: leave DATA_DIR and DATA_NAME both ""
# to use the dataset open in TopSpin, and TEMPLATE_EXPNO = None to use the expno open
# in TopSpin as the template.
DATA_DIR       = ""          # e.g. "/opt/nmrdata/rsh"
DATA_NAME      = ""          # e.g. "2610_4"
TEMPLATE_EXPNO = None        # e.g. 10

START_EXPNO = 700            # first new expno; all planned expnos must be free
REPEATS     = 1              # sets; each set occupies its own block of expnos

# OFF reference position within each set: "start", "end", "both", or "none"
# (the viewer divides by the start OFF; "both" also shows the drift over the set)
OFF_MODE = "both"

FREQ = None                  # GHz, e.g. the frequency of the largest enhancement in the profile

# Powers, in acquisition order: set one of the two lists, and leave the other None.
# A scrambled order (e.g. [1.0, 0.2, 0.65, 0.1, 0.8, 0.35, 0.5]) separates a drift
# over the run from the effect of the power.
POWER_FRACTIONS = [0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 1.0]   # of the power at 0.4 V
VOLTAGES        = None       # e.g. [0.10, 0.15, 0.20, 0.25, 0.30, 0.40] (V)
POWER_CAL       = None       # calibration file; None = /opt/dnptools/awg_power_cal.txt

D1        = 20               # s, set on every record (see above)
DS        = 0                # dummy scans, set on every record
ON_SCANS  = 4                # scans per ON record
OFF_SCANS = 16               # scans per OFF record

AWG_SETTLE = 2               # s after each AWG command, before the record is set up

# Record timing, as for profiles (normally left as they are)
SCAN_OVERHEAD  = 5     # s per scan beyond D1 (estimate and deadline)
POLL_INTERVAL  = 5     # s between completion checks
MAX_EXTRA_WAIT = 300   # s past the expected end before the run is stopped
POST_ACQ_PAD   = 5     # s after completion, before the next AWG command
EST_OVERHEAD   = 5     # s per record for re/wrpa/parameters and zg start-up (estimate only)
AWG_RETRIES      = 3   # attempts per AWG command, 5 s apart
MAX_CONSEC_SKIPS = 3   # ON points skipped in a row (failed 'cw') before the run is stopped

# TopSpin commands run on each record once its acquisition has finished
PROCESS_CMDS = ["efp", "absn"]

# Live plot: intensity of each record, read by fs_plot.py from pdata/1/1r
PEAK_PPM        = 0          # centre of the intensity window (ppm); None = whole spectrum
PEAK_WINDOW_PPM = 20.0       # full width of the window (ppm)
INTENSITY_MODE  = "extreme"  # "extreme", "max" or "sum"
LAUNCH_VIEWER   = True
RESPAWN_VIEWER  = True
