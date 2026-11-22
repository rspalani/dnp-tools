# bu_p1_freqs.py  -  settings for bu.py: DNP build-ups of the P1-diamond powder sample at
# several mm-wave frequencies, at 100 K
#
# Run in TopSpin with:   bu p1_freqs
# Check FREQS, the dataset, START_EXPNO and the template expno before each run; the
# confirmation dialog shows them in large type, with the expnos and the total time. The
# template's pulse program must saturate before D1 (the same template as the 100 K build-up
# at 526.008 GHz, with its receiver gain). bu_template.py explains every setting.
#
# One build-up per frequency in FREQS, interleaved (FREQ_ORDER "by_d1"): at each D1, one
# record at every frequency in turn, so that a slow drift of the spectrometer over the run
# affects every frequency alike. The viewer fits each frequency's build-up separately
# ('Fit' and 'normalized' compare the build-up times directly).

# Short name used in the run folder name and the index. Leave it out to use
# <name> from the file name bu_<name>.py (the type is added to the folder name).
#RUN_LABEL = "name"

SAMPLE   = "Diamond P1 center"
MAS_INFO = "13 kHz MAS, 1.3 mm diamond(c-1-3) rotor, 100 K"

# Dataset and template expno. Values set here are used; leave DATA_DIR and
# DATA_NAME both "" to use the dataset open in TopSpin when the script starts,
# and TEMPLATE_EXPNO = None to use the expno open in TopSpin as the template
# (it must belong to that dataset). Every record is created from the template
# with wrpa; D1, NS and DS are then set for each record.
DATA_DIR       = "/opt/nmrdata/wiesnern"
DATA_NAME      = "2611_3"
TEMPLATE_EXPNO = 10          # its pulse program must saturate before D1

START_EXPNO = 600            # first new expno; all planned expnos must be free
REPEATS     = 1              # repeats of the whole plan, each in its own expnos

SERIES = "on"                # FREQS works with "on" only

# Frequencies (GHz), one build-up each. An entry can also be a (frequency, power) pair,
# e.g. (526.008, 0.147) for a build-up at 21.5 mW; plain entries get POWER.
# Enhancements from the 100 K profile of 2026-11-08 (about 5 min per point, maximum 213):
#   526.008  the positive maximum (the CW frequency of the chirp grid)
#   526.030  the steep side above the maximum, about half of it (enhancement about 107)
#   526.090  near the zero crossing (about 526.105), enhancement about 28; at 526.095 it is
#            about 18, and the slope there is about 2 per MHz
#   526.180  the negative maximum, about -180
# (525.985, on the low side of the positive lobe at about 0.9 of the maximum, is left out
# to keep the run near 12 h.)
FREQS      = [526.008, 526.030, 526.090, 526.180]
FREQ_ORDER = "by_d1"         # "by_d1": at each D1 every frequency in turn;
                             # "by_freq": the whole build-up of one frequency, then the next
POWER      = 0.4             # AWG drive voltage for the entries without their own (at most 0.4)

SCAN_OVERHEAD = 5            # s per scan beyond D1 (saturation block, pulses, acquisition);
                             # used for the time estimate, the deadline, and ns_for_time below

# Build-up times D1 (s). T_B at 526.008 GHz is about 40 min at 100 K, and the build-up is
# stretched, so the longest D1 is 7200 s (3 T_B) to pin the plateau, with 150 s to 7200 s
# about evenly spaced on a log scale: 150, 450, 1300, 3100, 7200 s. They are acquired in a
# mixed order rather than from short to long, so that a drift over the run does not run
# along the D1 axis of every curve; the viewer sorts them. About 13.8 h for four frequencies.
D1_LIST = [1300, 150, 7200, 450, 3100]

# Scans per record, in the order of D1_LIST: two at 150 s, where the signal near the zero
# crossing is smallest, otherwise one.
NS_LIST     = [1, 2, 1, 1, 1]
OFF_NS_LIST = None           # not used (no OFF records)
DS          = 0              # dummy scans, set on every record (with saturation, 0 is enough)

AWG_SETTLE = 2         # s after each AWG command, before the record is set up

# Record timing, as for frequency profiles: after zg the script waits (NS+DS)*D1,
# then checks every POLL_INTERVAL s for audita.txt; the record is accepted
# whenever audita.txt appears before (NS+DS)*(D1+SCAN_OVERHEAD) + MAX_EXTRA_WAIT s
# after zg, and otherwise the run is stopped (mm-wave 'stop', error box).
POLL_INTERVAL  = 5     # s between completion checks
MAX_EXTRA_WAIT = 300   # s past the expected end before the run is stopped
POST_ACQ_PAD   = 2     # s after completion, before the next AWG command
EST_OVERHEAD   = 3     # s per record for re/wrpa/parameters and zg start-up
                       # (used only for the time estimate)

AWG_RETRIES      = 3   # attempts per AWG command, 5 s apart
MAX_CONSEC_SKIPS = 3   # ON records skipped in a row (failed 'cw') before the run is stopped

# TopSpin commands run on each record once its acquisition has finished,
# before the next AWG command. Set to [] for no processing.
PROCESS_CMDS = ["efp", "absn"]

# Live plot: intensity of each record, read by dnp_viewer.py from pdata/1/1r
PEAK_PPM        = 26.0       # centre of the intensity window (ppm); None = whole spectrum
PEAK_WINDOW_PPM = 30.0       # full width of the window (ppm)
INTENSITY_MODE  = "extreme"  # "extreme": largest |value| in the window, sign kept
                             # "max"    : largest value (for magnitude spectra, 'mc')
                             # "sum"    : sum of the points in the window
LAUNCH_VIEWER   = True       # start dnp_viewer.py in the background when the run starts
RESPAWN_VIEWER  = True       # after each record, start it again if no viewer for this
                             # run is running (e.g. its window was closed)
