# chirp2d_template.py  -  template for the settings files of chirp2d.py (DNP enhancement
# over a grid of chirp widths and chirp times)
#
# To set up a new kind of chirp grid, copy this file in the same folder:
#     cp /opt/nmrdata/fs_settings/chirp2d_template.py /opt/nmrdata/fs_settings/chirp2d_<name>.py
# fill in the values, and run it from TopSpin's command line with
#     chirp2d <name>
# ('chirp2d' alone lists the chirp-grid settings files to choose from). This template
# itself is not run.
#
# Each set is an optional OFF record, one CW record at FREQ (the zero-width point, and the
# reference for the map's I_chirp/I_CW), one ON record per chirp of the grid
# WIDTHS_MHZ x TIMES_US, and an optional OFF record. A chirp record is sent
#     chirp FREQ <width MHz> <time us> CHIRP_SHAPE POWER
# to the AWG server, which repeats the chirp back to back for the whole record; the CW
# record is sent 'cw FREQ POWER'. The sweep rate of a chirp is width/time (twice that
# for the V shapes, which sweep the width twice per chirp).
#
# The viewer shows a map: chirp width across, chirp time up (log), one cell per chirp,
# coloured by I_chirp/I_CW (= eps_chirp/eps_CW, which needs no OFF record) or by
# I_on/I_off - 1 (which needs an OFF reference: a start OFF, or OFF_REF), with lines
# of constant sweep rate.
#
# OFF records: at long D1 an OFF record costs as much as a chirp. OFF_REF uses an OFF
# record of an earlier run instead (the same template, RG, and D1); the dialog warns
# if they differ.
#
# The file is Python: plain assignments, with frange(start, stop, step) and
# logspace(first, last, n) available. UPPERCASE names are settings; an UPPERCASE
# name that is not a known setting stops the run before anything starts. Settings
# left out take the defaults in /opt/dnptools/fs_core.py (CHIRP2D_SETTINGS).

# Short name used in the run folder name and the index. Leave it out to use
# chirp2d_<name> from the file name chirp2d_<name>.py.
#RUN_LABEL = "chirp2d_name"

SAMPLE   = "sample description"          # shown in the dialog, the titles and the plot
MAS_INFO = "MAS rate, rotor, temperature"

# Dataset and template expno, as for profiles: leave DATA_DIR and DATA_NAME both ""
# to use the dataset open in TopSpin, and TEMPLATE_EXPNO = None to use the expno open
# in TopSpin as the template.
DATA_DIR       = ""          # e.g. "/opt/nmrdata/rsh"
DATA_NAME      = ""          # e.g. "2611"
TEMPLATE_EXPNO = None        # e.g. 10

START_EXPNO = 1000           # first new expno; all planned expnos must be free
REPEATS     = 1              # sets; each set occupies its own block of expnos

# OFF records acquired by this run, within each set: "start", "end", "both", or "none";
# and/or an OFF record of an earlier run (an expno of this dataset, or the path of an
# expno folder, e.g. "/opt/nmrdata/rsh/2611/312"), used as the reference for I_on/I_off
OFF_MODE = "none"
OFF_REF  = None

FREQ  = None                 # GHz: centre of every chirp, and the CW frequency
POWER = 0.4                  # AWG drive voltage (V) for the chirps and the CW record (at most 0.4)

WIDTHS_MHZ  = [10, 20, 40, 80]   # chirp widths (MHz, at the mm-wave output)
TIMES_US    = [1, 2, 4, 8]       # chirp times (us)
CHIRP_SHAPE = "I"                # "I" increasing, "D" decreasing, "V", "IV" (inverted V)
RATE_RANGE  = None               # e.g. (2, 50): only the chirps with a sweep rate in this range
ORDER       = "center_out"       # "center_out": from the rate closest to RATE_CENTER outwards;
                                 # "grid": row by row (each chirp time, widths increasing)
RATE_CENTER = 10.0               # MHz/us
CW_RECORD   = True               # one CW record per set, before the chirps

D1        = 20               # s, set on every record
DS        = 0                # dummy scans, set on every record
ON_SCANS  = 1                # scans per CW and chirp record
OFF_SCANS = 1                # scans per OFF record

AWG_SETTLE = 5               # s after each AWG command (a chirp download takes a few seconds)

# Record timing, as for profiles (normally left as they are)
SCAN_OVERHEAD  = 5     # s per scan beyond D1 (estimate and deadline)
POLL_INTERVAL  = 5     # s between completion checks
MAX_EXTRA_WAIT = 300   # s past the expected end before the run is stopped
POST_ACQ_PAD   = 5     # s after completion, before the next AWG command
EST_OVERHEAD   = 5     # s per record for re/wrpa/parameters and zg start-up (estimate only)
AWG_RETRIES      = 3   # attempts per AWG command, 5 s apart
MAX_CONSEC_SKIPS = 3   # ON records skipped in a row (failed AWG command) before the run is stopped

# TopSpin commands run on each record once its acquisition has finished
PROCESS_CMDS = ["efp", "absn"]

# Live plot: intensity of each record, read by fs_plot.py from pdata/1/1r
PEAK_PPM        = 0          # centre of the intensity window (ppm); None = whole spectrum
PEAK_WINDOW_PPM = 20.0       # full width of the window (ppm)
INTENSITY_MODE  = "extreme"  # "extreme", "max" or "sum"
LAUNCH_VIEWER   = True
RESPAWN_VIEWER  = True
