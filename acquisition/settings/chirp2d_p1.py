# chirp2d_p1.py  -  settings for chirp2d.py: chirp widths x chirp times for the P1-diamond
# powder sample at 100 K, around a sweep rate of 10 MHz/us
#
# Run in TopSpin with:   chirp2d p1
# Check FREQ, the dataset, START_EXPNO and the template expno before each run; the
# confirmation dialog shows them in large type, with the grid, the order, and the rate
# of every chirp.
#
# The grid: widths 10, 20, 40, 80 MHz x times 1, 2, 4, 8 us, factor-2 steps on both
# axes, so the diagonal is the 10 MHz/us line (4 chirps) and the others are 5 and
# 20 MHz/us (3 each), 2.5 and 40 (2 each), and 1.25 and 80 (1 each). ORDER "center_out"
# takes the 10 MHz/us chirps first, then 5 and 20, and so on, so a run stopped early
# has the chirps closest to 10 MHz/us. With D1 3000 s (1.25 T_B at 100 K) and NS 1:
# the CW record and 16 chirps, 17 records of about 50 min, about 14.3 h. No OFF record
# is acquired (one would add 50 min): the map's I_chirp/I_CW needs none, and OFF_REF
# can point to an OFF record of an earlier run with the same RG and D1 for I_on/I_off - 1.
# chirp2d_template.py explains every setting.

#RUN_LABEL = "p1"

SAMPLE   = "Diamond P1 center"
MAS_INFO = "1.3 mm rotor, 100 K"

DATA_DIR       = ""
DATA_NAME      = ""
TEMPLATE_EXPNO = None

START_EXPNO = 1000
REPEATS     = 1
OFF_MODE    = "none"
OFF_REF     = None           # e.g. 312: an OFF record with the same template, RG, and D1 3000 s

FREQ  = 526.008
POWER = 0.4

WIDTHS_MHZ  = [10, 20, 40, 80]
TIMES_US    = [1, 2, 4, 8]
CHIRP_SHAPE = "I"
RATE_RANGE  = None
ORDER       = "center_out"
RATE_CENTER = 10.0
CW_RECORD   = True

D1        = 3000
DS        = 0
ON_SCANS  = 1
OFF_SCANS = 1

AWG_SETTLE     = 5
SCAN_OVERHEAD  = 5
POLL_INTERVAL  = 5
MAX_EXTRA_WAIT = 300
POST_ACQ_PAD   = 5
EST_OVERHEAD   = 5
AWG_RETRIES      = 3
MAX_CONSEC_SKIPS = 3

PROCESS_CMDS = ["efp", "absn"]

PEAK_PPM        = 26.0
PEAK_WINDOW_PPM = 10.0
INTENSITY_MODE  = "extreme"
LAUNCH_VIEWER   = True
RESPAWN_VIEWER  = True
