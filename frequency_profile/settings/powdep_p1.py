# powdep_p1.py  -  settings for powdep.py: DNP enhancement against mm-wave power for the
# P1-diamond powder sample
#
# Run in TopSpin with:   powdep p1
# Set FREQ (below) to the frequency to irradiate at, set D1 for the temperature (see
# powdep_template.py), and check the dataset, START_EXPNO and the template expno before
# each run; the confirmation dialog shows them in large type, with the voltage and power
# of every point. With D1 300 s, NS 1 for ON and 16 for OFF, and 8 powers, a set takes
# about 3.4 h. powdep_template.py explains every setting.

#RUN_LABEL = "powdep_p1"

SAMPLE   = "Diamond P1 center"
MAS_INFO = "15 kHz MAS, 1.3 mm diamond(c-3-1) rotor, RT"

DATA_DIR       = ""
DATA_NAME      = ""
TEMPLATE_EXPNO = None

START_EXPNO = 700
REPEATS     = 1
OFF_MODE    = "both"

FREQ = None                  # GHz: set before the first run

POWER_FRACTIONS = [0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 1.0]   # of the power at 0.4 V
VOLTAGES        = None

D1        = 300
DS        = 0
ON_SCANS  = 1
OFF_SCANS = 16

AWG_SETTLE     = 2
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
