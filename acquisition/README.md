# DNP frequency profiles, build-ups, decays, power dependences, and chirp grids

Acquisition and live display of DNP frequency profiles, build-up curves,
decays, power dependences, and chirp grids on the 800 MHz DNP spectrometer (TopSpin 3.6.2). For a profile, a TopSpin
script steps the mm-wave frequency through the AWG, acquires and processes one
record per frequency, and a viewer plots the enhancement against frequency while
the records come in. For a build-up, a second script acquires one record per
build-up time D1, at one frequency or with the microwaves off, and the viewer
plots and fits the intensity against D1. For a decay, a third script polarizes
with the microwaves on, switches them off, and acquires small-flip-angle records
at set times afterwards; the viewer fits the decay back to equilibrium. For a
power dependence, a fourth script acquires one record per AWG drive voltage at
one frequency, and the viewer plots the enhancement against the mm-wave power
from the source's calibration. For a chirp grid, a fifth script acquires one
record per chirp width and chirp time at one centre frequency, plus a CW
record, and the viewer shows the enhancement as a map over width and time.
Another TopSpin script applies the phase set in the viewer to the TopSpin data
after a run.

The headers of `dnp_core.py`, `dnp_viewer.py`, and `dnp_rephase_core.py` describe in
detail what each program does; this page covers installation and use.

## Files

| In this folder | Installed as | What it is |
|---|---|---|
| `dnptools/dnp_core.py` | `/opt/dnptools/dnp_core.py` | Acquisition code (TopSpin/Jython), for profiles, build-ups, decays, power dependences, and chirp grids: plan, checks, confirmation dialog, AWG commands, records, run folder, viewer |
| `dnptools/dnp_viewer.py` | `/opt/dnptools/dnp_viewer.py` | Viewer (Python 3): profile, build-up, decay, power dependence, or chirp map with fits, one record at a time, phase/baseline/window, exports |
| `dnptools/awg_power_cal.txt` | `/opt/dnptools/awg_power_cal.txt` | Output power of the 527 GHz source against the AWG drive voltage (for power dependences) |
| `dnptools/dnp_rephase_core.py` | `/opt/dnptools/dnp_rephase_core.py` | Post-run phasing of the TopSpin data with the viewer's phase |
| `dnptools/awg_cmd.py` | `/opt/dnptools/awg_cmd.py` | Sends one command to the AWG control server (set its address; see below) |
| `topspin/fs.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/fs.py` | TopSpin command `fs <name>` (profile) |
| `topspin/bu.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/bu.py` | TopSpin command `bu <name>` (build-up) |
| `topspin/decay.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/decay.py` | TopSpin command `decay <name>` (decay) |
| `topspin/powdep.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/powdep.py` | TopSpin command `powdep <name>` (power dependence) |
| `topspin/chirp2d.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/chirp2d.py` | TopSpin command `chirp2d <name>` (chirp grid) |
| `topspin/fs_rephase.py`, `dnp_rephase.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/` | TopSpin command `fs_rephase` (also `dnp_rephase`) |
| `settings/fs_template.py` | `/opt/nmrdata/dnp_settings/` | Template for the settings files, one per kind of experiment |
| `settings/fs_p1.py`, `fs_bdpa.py`, `fs_nox.py` | `/opt/nmrdata/dnp_settings/` | Settings for the P1 diamond, BDPA, and m-TinyPol profiles |
| `settings/bu_template.py` | `/opt/nmrdata/dnp_settings/` | Template for the build-up settings files |
| `settings/bu_p1.py`, `bu_bdpa.py`, `bu_nox.py` | `/opt/nmrdata/dnp_settings/` | Build-up settings for the same samples (set `FREQ` before the first run) |
| `settings/bu_p1_freqs.py` | `/opt/nmrdata/dnp_settings/` | Build-ups of the P1-diamond sample at four frequencies at 100 K (`FREQS`) |
| `settings/decay_template.py` | `/opt/nmrdata/dnp_settings/` | Template for the decay settings files |
| `settings/decay_p1.py` | `/opt/nmrdata/dnp_settings/` | Decay settings for the P1 diamond at 100 K (set `FREQ` before the first run) |
| `settings/powdep_template.py` | `/opt/nmrdata/dnp_settings/` | Template for the power-dependence settings files |
| `settings/powdep_p1.py` | `/opt/nmrdata/dnp_settings/` | Power-dependence settings for the P1 diamond (set `FREQ` and D1 before the first run) |
| `settings/chirp2d_template.py` | `/opt/nmrdata/dnp_settings/` | Template for the chirp-grid settings files |
| `settings/chirp2d_p1.py` | `/opt/nmrdata/dnp_settings/` | Chirp grid for the P1 diamond at 100 K: 526.008 GHz, 10 to 80 MHz x 1 to 8 µs, D1 3000 s (about 14.3 h) |

The TopSpin scripts only start the code in `/opt/dnptools` (with `execfile`,
so that TopSpin always runs the current version without being restarted).

## Requirements

- TopSpin 3.6.2 (its Jython 2.7 runs `fs.py`, `bu.py`, `decay.py`, `powdep.py`, `chirp2d.py`, and `fs_rephase.py`).
- `python` on the PATH, Python 2.7 or 3, for `awg_cmd.py`.
- For the viewer: `/usr/bin/python3` (3.6 or newer) with `numpy`, `matplotlib`
  (3.3 or newer), and `python3-tk`. Without a display the viewer writes its
  files only. Keep the code compatible with Python 3.6 and matplotlib 3.3, the
  versions on the spectrometer PC.

## Installation and updates

Updates are installed with one command, as nmrsu on the spectrometer PC (it asks
for the sudo password to write in `/opt`):

```bash
bash /home/nmrsu/src/dnp-tools/deploy/update.sh --dry-run   # what would change
bash /home/nmrsu/src/dnp-tools/deploy/update.sh             # update to the latest main
```

[`deploy/update.sh`](../deploy/update.sh) pulls the latest `main` into the clone in
`/home/nmrsu/src/dnp-tools` (the first time, it makes the clone; a folder there that
is not a git clone, such as an unpacked tarball, is moved aside), and stops if the run
index shows a run in progress (`--force` overrides). It then copies:

| From the repository | To |
|---|---|
| `dnptools/dnp_core.py`, `dnp_viewer.py`, `dnp_rephase_core.py` | `/opt/dnptools/` |
| `topspin/*.py` | `/opt/topspin3.6.2/exp/stan/nmr/py/user/` |
| `dnp_monitor.py`, `dnp_logviewer.py` (top folder) | `/opt/dnptools/dnp_monitor/` |
| `dnptools/awg_cmd.py`, `awg_power_cal.txt` | `/opt/dnptools/`, only if not there yet |
| `settings/*.py` | `/opt/nmrdata/dnp_settings/`, only if not there yet |
| (on the spectrometer) `/opt/nmrdata/fs_settings/*.py` | `/opt/nmrdata/dnp_settings/` under the new names, only if not there yet |

Every file it replaces is kept in `/opt/dnptools/backup/<date>/`, together with
`restore.sh`, which puts those files back: `sudo bash /opt/dnptools/backup/<date>/restore.sh`
undoes that update. The site files,
`awg_cmd.py` with the AWG address, `awg_power_cal.txt`, and the settings files
edited on the spectrometer, are never overwritten; to replace one with the
repository's version, copy it by hand. On a new installation, set `HOST` (and
`PORT`) in `/opt/dnptools/awg_cmd.py` to the AWG control server's address.

The script writes the installed commit to `/opt/dnptools/VERSION`, and every run
copies that line into its `run.txt` as `# code_version`, so each run can be traced
to the code that acquired it.

A viewer that is already open keeps running the old code; close it and reopen
it with the command shown in its window.

### Names since November 2026

Until November 2026 the names came from the first experiment type, the
frequency sweep (fs). They are now the same for every type:

| Before | Now |
|---|---|
| `/opt/nmrdata/fs_settings/` | `/opt/nmrdata/dnp_settings/` |
| `settings_<name>.py` (profile), `buildup_<name>.py` (build-up) | `fs_<name>.py`, `bu_<name>.py`; `decay_`, `powdep_`, `chirp2d_` as before |
| `<dataset>/fs_runs/<YYYYMMDD-HHMMSS>_<label>_e<expno>/` | `<dataset>/dnp_runs/<name>_<type>_<YYYYMMDD-HHMMSS>_e<expno>/` |
| `/opt/nmrdata/fs_runs.tsv` | `/opt/nmrdata/dnp_runs.tsv` (same columns, plus `type` at the end) |
| `/opt/dnptools/fs_core.py`, `fs_plot.py`, `fs_rephase_core.py` | `dnp_core.py`, `dnp_viewer.py`, `dnp_rephase_core.py` |
| `frequency_profile/` in this repository | `acquisition/` |

The TopSpin commands are typed as before (`fs p1`, `bu p1`, `decay p1`, ...).
The first update with the new names copies every settings file of
`fs_settings` into `dnp_settings` under its new name, unchanged and with its
date, so values edited on the spectrometer carry over. After that only
`dnp_settings` is read:

- an old name still works (`bu buildup_p1`, or a file `buildup_x.py` in
  `dnp_settings`); the confirmation dialog says what the new name is;
- a settings file that is only in `fs_settings` is not run; the message gives
  the `cp` command that copies it to `dnp_settings`;
- if a file in `fs_settings` was changed after it was copied, nothing is run
  and the message names both files, so an edit made in the old folder out of
  habit is not silently ignored.

`fs_settings`, `fs_runs.tsv`, the old run folders and the old programs in
`/opt/dnptools` are left as they are: the viewer reads old and new run folders,
and `restore.sh` of that update returns the TopSpin commands to the old
programs. A `RUN_LABEL` set in a settings file loses a leading `<type>_`
(`bu_p1` becomes `p1`), because the type is now in the folder name. Old run
folders are renamed later, once the new names have been checked on the copy on
fbml-rsp.

## Running a profile

1. Make a settings file for the kind of experiment, or use an existing one:

   ```bash
   cp /opt/nmrdata/dnp_settings/fs_template.py /opt/nmrdata/dnp_settings/fs_<name>.py
   ```

   It is Python with plain assignments: `SAMPLE`, `MAS_INFO`, the dataset
   (`DATA_DIR`, `DATA_NAME`, `TEMPLATE_EXPNO`; left empty, the dataset and
   expno open in TopSpin are used), `START_EXPNO`, `REPEATS`, `OFF_MODE`, the
   frequencies `FREQS` (with `frange(start, stop, step)`), `D1`, `PROFILE_NS`,
   `OFF_SCANS`, and the processing commands. An UPPERCASE name that is not a
   known setting stops the run before anything starts, so typos are caught.
2. In TopSpin, open the dataset and template expno if the settings file leaves
   them empty, and type `fs <name>` (`fs` alone lists the settings files).
3. The confirmation dialog shows the dataset, the new expnos, and the template.
   The script checks that all planned expnos are free, before the dialog and
   again after OK.
4. The viewer opens by itself. If its window is closed, it is opened again
   after the next record.

Each run gets a folder inside the dataset,
`<dataset>/dnp_runs/<name>_fs_<YYYYMMDD-HHMMSS>_e<start expno>/` (for example
`p1_fs_20261122-210455_e300`), with `run.txt`
(one line per finished record), `log.txt`, `settings.txt` (every setting as
used), a copy of the settings file, and the viewer's files (`viewer.log`,
`plot.png`, `values.tsv`, `phase.txt`, and `records.csv` and `profile.eps` when
exported). The folder travels with the dataset when it is copied. One line per
run start and end is added to `/opt/nmrdata/dnp_runs.tsv`. `<name>` is the
`<name>` of `fs_<name>.py`, or `RUN_LABEL` if the settings file sets it.

## Running a build-up

A build-up acquires one record per build-up time D1. The template's pulse
program must saturate before D1, so that every scan starts from zero
polarization and D1 is the build-up time.

1. Make a build-up settings file, or use an existing one:

   ```bash
   cp /opt/nmrdata/dnp_settings/bu_template.py /opt/nmrdata/dnp_settings/bu_<name>.py
   ```

   It has the same dataset, template, timing, and live-plot settings as a
   profile, and instead of the frequencies:
   - `SERIES`: the records of each set: `"on"` (microwaves at `FREQ`), `"off"`,
     `"interleaved"` (ON and OFF at each D1, back to back; only where the OFF
     signal can be measured at every D1), `"on_then_off"`, or `"off_then_on"`.
   - `FREQ` (GHz) and `POWER`: the AWG's `cw` command, sent before each ON
     record (`stop` is sent before each OFF record). The example files have
     `FREQ = None`, so that a run cannot start before a frequency is chosen.
   - `D1_LIST`: the build-up times in s, acquired in the order written.
     `logspace(first, last, n)` gives `n` log-spaced values; about 0.05 to 5
     times the expected T_B covers the curve and its plateau.
   - `NS_LIST` (and `OFF_NS_LIST` for the OFF records): one number of scans
     for all, or one per D1. `ns_for_time(D1_LIST, seconds, ns_max=...,
     multiple=..., overhead=SCAN_OVERHEAD)` gives records of about `seconds`
     each, with more scans at short D1, rounded to a multiple of the phase
     cycle.

   The examples: `bu_p1.py` (room temperature, T_B expected at 6–7 min:
   D1 15 to 2000 s, about 2 h; a comment gives values for 100 K),
   `bu_bdpa.py` (100 K, T_B about 30 s: D1 1 to 150 s, about 40 min), and
   `bu_nox.py` (100 K, T_B 6–7 s: D1 0.25 to 35 s, about 25 min), each
   with `SERIES = "on"`.
2. In TopSpin, type `bu <name>` (`bu` alone lists the build-up settings files).
   If `bu` runs something else on this TopSpin, the name is taken: rename
   `bu.py` (e.g. to `fsbu.py`) and type that name instead.
3. The confirmation dialog lists the plan, the mm-wave setting, every D1 with
   its NS, and the expected duration; the expno checks are as for a profile.

### Build-ups at several frequencies

`FREQS` in place of `FREQ` acquires one build-up per frequency in one run, with
`SERIES = "on"`. An entry is a frequency in GHz, which gets `POWER`, or a
`(frequency, power)` pair, e.g. `(526.008, 0.147)` for a build-up at lower power.
`FREQ_ORDER = "by_d1"` (default) acquires, at each D1, one record at every
frequency in turn, so that a slow drift of the spectrometer affects every
frequency alike; `"by_freq"` acquires the whole build-up of one frequency, then
the next. Each frequency is its own set (set k for the k-th entry of `FREQS`;
with `REPEATS` > 1 the repeats follow as further sets in the same order), the
expnos run in acquisition order, and `run.txt` lists the frequency and power of
each set (`# set_cw`). The viewer fits each frequency separately and names the
series by frequency; with "Error bars: repeats" the mean is over the repeats of
the same frequency. Writing `D1_LIST` in a mixed order, rather than from short to
long, keeps a drift from running along the D1 axis of every curve.
`bu_p1_freqs.py` is the example: the P1-diamond sample at 100 K, four
frequencies across the profile, D1 150 to 7200 s in a mixed order, about 13.8 h.

The run folder is in `dnp_runs` as for a profile, `<name>_bu_<time>_e<expno>`; `run.txt`
has `# type = buildup` and the D1 of each record, and `settings.txt` lists every
planned record with its expected duration (the viewer uses it for the expected
end). A profile settings file given to `bu`, or a build-up file given to `fs`,
is refused with a message that says which command to use.

## Running a decay

A decay follows the polarization back to equilibrium after the microwaves are
switched off. One run (per set, `REPEATS` sets one after the other):

1. `cw FREQ POWER` is sent to the AWG and the sample polarizes for
   `POLARIZE_TIME` s.
2. A reference record is acquired with the microwaves still on: the
   steady-state signal.
3. `stop` is sent to the AWG; this is t = 0.
4. One record is acquired at each time in `TIMES_LIST` after t = 0. The script
   copies the template, sets D1 so that the pulse comes at the target time, and
   writes the time actually reached to `run.txt`.

Every record has NS 1 and DS 0. The template's pulse program must not saturate,
and its pulse should be a small flip angle (e.g. 5°), so that each record uses
only a small part of the polarization: cos(flip angle) of it remains after each
pulse (16 pulses of 5° leave 0.94), and the viewer corrects for this. Set RG in
the template for the reference, the largest signal of the run.

1. Make a decay settings file, or use `decay_p1.py`:

   ```bash
   cp /opt/nmrdata/dnp_settings/decay_template.py /opt/nmrdata/dnp_settings/decay_<name>.py
   ```

   It has the same dataset, template, and live-plot settings as a build-up,
   and instead of the D1 values:
   - `FREQ` (GHz) and `POWER`: the AWG's `cw` command for the polarization
     (`FREQ = None` in the files here, so that a run cannot start before a
     frequency is chosen).
   - `POLARIZE_TIME`: s from `cw` to the reference pulse, about 5 times T_B.
   - `TIMES_LIST`: the target times in s after t = 0, increasing;
     `logspace(first, last, n)` gives `n` log-spaced values. Out to about 3 T1
     lets the viewer fit the equilibrium level as well.
   - `FLIP_DEG`: the template's flip angle, written to the run file for the
     viewer's correction.

   `decay_p1.py`: 3 h of polarization and 15 records from 30 s to 9000 s,
   about 5.5 h in all.
2. In TopSpin, type `decay <name>` (`decay` alone lists the decay settings
   files). If `decay` runs something else on this TopSpin, the name is taken:
   rename `decay.py` and type the new name instead.
3. The confirmation dialog lists the plan, the mm-wave setting, the target
   times (with a warning when some are closer together than a record can be
   set up), and the expected duration.

Timing: each record needs a few seconds besides D1 (copying the template,
setting parameters, starting `zg`, processing). The script measures this
latency on every record (from the end of acquisition less AQ) and uses the
median so far for the next D1, starting from `ZG_LATENCY`. A target that comes
sooner than the previous record allows is taken as soon as possible, logged,
and recorded with its actual time. Times are accurate to about a second, so
decays of a minute or longer are followed well; faster decays need a pseudo-2D
pulse program instead.

The run folder is `<name>_decay_<time>_e<expno>`; `run.txt` has `# type = decay`, the
flip angle, and for each record its D1, its time t after the microwaves went
off, and the target time. A decay file given to `fs` or `bu`, or another
settings file given to `decay`, is refused with a message that says which
command to use.

## Running a power dependence

A power dependence is a profile at one frequency in which the AWG drive voltage
(the second argument of `cw`) changes from record to record. Each set
(`REPEATS`) is an optional OFF record, one ON record per voltage, and an
optional OFF record, placed by `OFF_MODE` as in a profile; the viewer plots
I_on/I_off − 1 with the start OFF of the set.

Full drive is 0.4 V. No script sends more: `powdep` refuses a larger voltage,
and `fs`, `bu`, and `decay` refuse a `POWER` above 0.4 before anything starts.

The voltages come from one of two settings:
- `POWER_FRACTIONS`: fractions of the power at full drive. The script converts
  them to voltages (rounded to 1 mV) with the source's calibration,
  `/opt/dnptools/awg_power_cal.txt`, by a monotone cubic interpolation. The
  source saturates near full drive (97% of full power at 0.35 V), so this spaces
  the points in power, where evenly spaced voltages would crowd them at the top.
- `VOLTAGES`: the drive voltages in V, used as given.

The calibration was measured at 526.012 GHz (AWG 1.903 GHz): drive voltage in
mV against output power in mW, from 100 to 450 mV. The ratio P(V)/P(0.4 V) is
taken to hold at every frequency, the absolute mW only at 526.012 GHz. Voltages
below the first calibration point (100 mV, 9% of full power) are refused, since
their power is not known; add points to the file to go lower. Each run copies
the table into its `run.txt`, so a later change to the file does not change
old runs.

1. Make a settings file, or use `powdep_p1.py`:

   ```bash
   cp /opt/nmrdata/dnp_settings/powdep_template.py /opt/nmrdata/dnp_settings/powdep_<name>.py
   ```

   Besides the dataset, template, and live-plot settings of a profile it has
   `FREQ` (GHz), one of `POWER_FRACTIONS` and `VOLTAGES`, `D1`, `ON_SCANS`,
   and `OFF_SCANS`. T_B shortens as the power rises, so D1 gives the
   steady-state enhancement at every power only if it is several T_B at the
   lowest power; a shorter D1 mixes the enhancement with the build-up rate. A
   scrambled order of the powers separates a drift over the run from the effect
   of the power.
2. In TopSpin, type `powdep <name>` (`powdep` alone lists the files).
3. The confirmation dialog lists every point as drive voltage, fraction of full
   power, and mW at the calibration frequency, in acquisition order.

The run folder is `<name>_powdep_<time>_e<expno>`; `run.txt` has `# type = powdep`,
the calibration, and the drive voltage of each record in an eighth column.

## Running a chirp grid

A chirp grid measures the enhancement at one centre frequency for every
combination of a list of chirp widths and a list of chirp times. Each set
(`REPEATS`) is an optional OFF record, one CW record at `FREQ`, one ON record
per chirp, and an optional OFF record. The AWG server gets
`chirp FREQ <width MHz> <time µs> <shape> POWER` for a chirp record (it repeats
the chirp back to back for the whole record) and `cw FREQ POWER` for the CW
record. The sweep rate of a chirp is width/time, or twice that for the V and
inverted-V shapes, which sweep the width twice per chirp.

The CW record is the reference of the map: I_chirp/I_CW equals ε_chirp/ε_CW
for large enhancements and needs no OFF record. At a D1 of tens of minutes an
OFF record costs as much as a chirp, so `chirp2d_p1.py` acquires none; for
I_on/I_off − 1, set `OFF_REF` to an OFF record of an earlier run (next section),
or `OFF_MODE` to acquire one.

1. Make a settings file, or use `chirp2d_p1.py`:

   ```bash
   cp /opt/nmrdata/dnp_settings/chirp2d_template.py /opt/nmrdata/dnp_settings/chirp2d_<name>.py
   ```

   Besides the dataset, template, and live-plot settings of a profile it has
   `FREQ` (GHz), `POWER` (AWG drive voltage, default and maximum 0.4 V),
   `WIDTHS_MHZ`, `TIMES_US`, `CHIRP_SHAPE` (`I` increasing, the default; `D`,
   `V`, `IV`), `D1`, `ON_SCANS`, and `OFF_SCANS`. `RATE_RANGE = (lo, hi)` keeps
   only the chirps whose sweep rate (MHz/µs) lies in that range. `ORDER =
   "center_out"` acquires the chirps from the rate closest to `RATE_CENTER`
   outwards, so that a run stopped early has the chirps of most interest;
   `"grid"` goes row by row.
2. In TopSpin, type `chirp2d <name>` (`chirp2d` alone lists the files).
3. The confirmation dialog shows the grid as a table with the acquisition order
   and sweep rate of each cell (cells outside `RATE_RANGE` grey), and the total
   time.

`chirp2d_p1.py` (P1 diamond at 100 K, T_B about 40 min): 526.008 GHz, widths
10, 20, 40, 80 MHz and times 1, 2, 4, 8 µs, D1 3000 s (1.25 T_B), one scan,
no OFF. Factor-2 steps on both axes put four chirps on the 10 MHz/µs diagonal,
three each on 5 and 20 MHz/µs, two on 2.5 and 40, and one on 1.25 and 80; with
the CW record that is 17 records of about 50 min, about 14.3 h. Check `FREQ`,
the dataset, `START_EXPNO`, and the template before the run.

The run folder is `<name>_chirp2d_<time>_e<expno>`; `run.txt` has `# type = chirp2d`,
the grid, the chirps in acquisition order (`# chirps`), and the chirp width
(MHz) and time (µs) of each record in two more columns (width 0 for the CW
record).

## An OFF record from an earlier run (`OFF_REF`)

In `fs`, `powdep`, and `chirp2d` settings, `OFF_REF` names an OFF record that
is already acquired: an expno of the run's dataset (`OFF_REF = 312`) or the
path of an expno folder in another dataset
(`OFF_REF = "/opt/nmrdata/rsh/2611/312"`). The viewer then takes I_off from it,
processed with the same viewer settings as the run's own records, for every
set. `OFF_MODE` still acquires OFF records at the start and/or end of each set
if asked; with a reference they serve as drift checks and are listed as a
multiple of the reference.

Before the run, the script checks that the record has a processed spectrum
(`pdata/1/1r`) and compares the RG, P1, PLW1, and pulse program it was acquired
with (its `acqus`) with the template's current ones (its `acqu`, which the new
records get), and its D1 with the run's `D1`; a difference appears as a warning
in the confirmation dialog, which can still be accepted. If the reference's own
`acqu` disagrees with its `acqus`, the warning gives both. An OFF record taken with
another D1 or receiver gain does not give the enhancement. `run.txt` has
`# off_ref = <expno folder>`.

## The viewer

It opens by itself during a run; to open it later, for any run:

```bash
python3 /opt/dnptools/dnp_viewer.py <dataset>/dnp_runs/<run folder>/run.txt
```

(the exact command is shown in the window and in `viewer.log`). With `--once`,
or without a display, it writes `plot.png` and `values.tsv` and exits;
`--csv` also writes `records.csv`.

- The top bar has the "Reopen" command (to copy), "Also plot", "Export", and
  "Hide spectrum", which hides the whole spectrum side and leaves the profile
  across the window ("Show spectrum" brings it back).
- Above the profile, the run's status: a blinking red dot and "Experiment
  running" (with the record reached out of those planned, and the expected
  end), "Finished", "Stopped before the end" in red when the run was aborted
  or stopped from TopSpin, or an amber "No new record for N min". "Live"
  refreshes the window every 15 s; it turns itself off when the run ends and
  is off when an ended run is opened. "Refresh" updates the window once, for
  example after reprocessing in TopSpin. Below the status, one row each for
  the run, the intensity measure and processing, the OFF records, and any
  warnings.
- The profile is on the left and one record on the right, with a divider that
  can be dragged. The right side follows the latest record while
  "Follow latest" is ticked; a record chosen in the list, with "< Prev" and
  "Next >" (or Page Up and Page Down), or by clicking a point of the profile
  is shown instead.
- The controls along the bottom ("Hide controls" under the spectrum hides
  them) try settings on the record shown: zero- and first-order phase with a
  pivot, magnitude, polynomial baseline, the
  intensity window (typed, or dragged with the right mouse button), and the
  intensity measure. "Apply to all records" applies them to the whole profile.
  All of this is in the viewer only; the TopSpin data are unchanged until
  `fs_rephase` is run.
- Intensity measures: `extreme` (largest |value| in the window, sign kept),
  `max`, `sum`, and `FID(t0)`, a diagnostic that uses the start of the raw FID
  instead of the spectrum (independent of phase, window, and baseline), with
  the FID phase as an optional panel below the profile.
- "Also plot" adds the integral of the window, or the FID phase.
- "Export: Profile EPS" writes `profile.eps` for Adobe Illustrator (Helvetica
  text, one path per trace and per marker, no clipping masks), 7 in wide, the
  full page width of ACS journals (Elsevier's is 190 mm), and as high as the
  profile on screen is in proportion (2 to 5 in). "Export: CSV" writes
  `records.csv` (one row per record, with FID(t0), the FID phase, and the
  window integrals).
- The window's size and position, the divider, and whether the spectrum side
  is shown are saved in `~/.config/fs_plot/window.txt`, so the next viewer
  opens the same way.

### Build-up runs in the viewer

The viewer recognizes a build-up run by its `run.txt` and plots the intensity
per scan (or FID(t0)) against D1: ON as filled circles, OFF as open squares,
each series with its fitted curve. With both ON and OFF shown, OFF has its own
axis on the right.

- "Fit" chooses the model, fitted to each series by least squares weighted by
  NS (the noise of an intensity per scan goes as 1/√NS), with standard errors
  from the scatter about the fit:
  - mono-exponential (default), S∞·(1 − exp(−D1/T_B));
  - mono-exponential with a free start, S∞ − (S∞ − S₀)·exp(−D1/T_B), for a
    saturation that leaves a residual S₀;
  - stretched exponential, S∞·(1 − exp(−(D1/T_B)^β)), β between 0.1 and 3;
  - bi-exponential, S₁·(1 − exp(−D1/T₁)) + S₂·(1 − exp(−D1/T₂)).
- Each fitted series gets one row above the plot: the build-up time(s), S∞,
  the other parameters, and the largest signal per square root of time, S/√t,
  with the D1 where it occurs (1.26 T_B for the mono-exponential). With ON and
  OFF in the same set, an "ON/OFF" row gives the ratios of S∞ and of the
  largest S/√t. A fit whose build-up time lies beyond the range the D1 values
  can determine (for example while a run has only reached the rising part) is
  shown as "not determined", with a dashed curve and no ratios; a "Note" row
  says when S∞ is extrapolated beyond the longest D1.
- "log D1" makes the D1 axis logarithmic; "normalized" divides each series by
  its fitted S∞, on one axis, to compare the build-up times.
- A run with several frequencies (`FREQS`) has one series per frequency, named
  by its frequency (and power, where the powers differ); `values.tsv` lists the
  frequency and power of each set in its header.
- The record pane, its settings, "Apply to all records", FID(t0), and the FID
  phase work as for a profile; the window integral is not plotted.
- "Export: Build-up EPS" writes `buildup.eps` (as shown, same format as the
  profile EPS). `values.tsv` has the D1 and the fitted value of each record and
  the fit results in its header; `records.csv` has a `d1_s` column.
- The expected end of a running build-up is the sum of the expected durations
  of the records still to come, and the amber "No new record" appears only when
  the next record is overdue, so a long record late in the run is not reported
  as a problem.

### Decay runs in the viewer

The viewer plots the intensity per scan (or FID(t0)) against the time after
the microwaves went off: the reference as an open diamond at t = 0 (drawn at
the left edge with "log t"), the decay records as filled circles, each set
with its fitted curve.

- "Fit" chooses the model; each record is corrected for the pulses before it
  (cos(flip angle) each):
  - mono-exponential (default), S_eq + (S₀ − S_eq)·exp(−t/T₁), exact including
    the thermal polarization that the pulses also take;
  - stretched exponential, S_eq + (S₀ − S_eq)·exp(−(t/T₁)^β);
  - bi-exponential, S_eq + S₁·exp(−t/T₁) + S₂·exp(−t/T₂).
- The plot shows the fitted curve as sampled (solid) and the decay without the
  pulses' losses (dotted), which is what T₁ describes. In a simulated run
  (T₁ 300 s, 15 pulses of 5° from 10 to 1500 s), leaving out the correction
  gave a T₁ 5% too short.
- The row below the top bar has "S_eq" and "flip angle". S_eq empty: fitted. A
  value fixes it, in the units of the plot (intensity per scan, or FID(t0) per
  NS·RG), for a decay not followed long enough to fit it; the fit row says when
  the last time is too short for S_eq to be fitted well. A record of the same
  template at thermal equilibrium, with more scans, gives this value. The flip
  angle, empty, is the one in the run file.
- The fit row gives T₁ (or T₁ and T₂), S₀, S_eq, and S₀/S_eq, the
  enhancement left at t = 0 relative to equilibrium. A "Timing" row says how
  close the records came to their target times.
- "normalized" divides each set by its fitted S₀. Error bars, the 1/σ²
  weights, the record pane, FID(t0), and the exports work as for a build-up;
  "Export: Decay EPS" writes `decay.eps`, `values.tsv` has t and the fitted
  value of each record, and `records.csv` has `d1_s`, `t_s`, and `target_s`.
- With `extreme` or `max`, weak points are biased upward by noise (the largest
  of many noisy points); for a tail near the noise level, `sum` or FID(t0)
  avoids this bias.

### Power-dependence runs in the viewer

- **Axes:** the x axis is the fraction of full power, P/P_full, with the power in
  mW (from the calibration, valid at its frequency) under each tick. The drive
  voltage of each point is along the top. "√P" plots against √(P/P_full)
  instead, which is proportional to the mm-wave field.
- **Fit:** "saturation" fits y = A·P/(P + P½) to each set, or to the means with
  "repeats" error bars; "none" shows the points only. For intensities (no
  start OFF), the fit is y₀ + A·P/(P + P½). The fit row gives A, P½ as a
  fraction and in mW, and the share of A that full power reaches. It notes when
  P½ lies above the highest power measured, so that A is an extrapolation.
- **The rest** works as for a profile: integral, FID phase, FID(t0), error bars
  and the 1/σ² weights, click-to-record, and the CSV.
- **Exports:** "Export: Power EPS" writes `powdep.eps`. `values.tsv` adds
  `drive_V`, `power_fraction`, `power_mW_cal`, and `y_fit`; `records.csv` adds
  the first three.

### Chirp runs in the viewer

- **Map:** chirp width across (logarithmic; untick "log width" for linear),
  chirp time up (logarithmic), one cell per chirp with its value written in it.
  A cell is empty until its record arrives, and hatched if it is not in the
  plan (left out by `RATE_RANGE`). Dashed lines mark constant sweep rates
  (1, 3, 10, 30, 100 MHz/µs, computed as 2 × width/time for the V shapes). The
  latest chirp is outlined in red.
- **Map** in the top bar sets the colour: ε_chirp/ε_CW (I_chirp/I_CW, with the
  CW record of the set; colours diverge about 1, red above) or I_on/I_off − 1
  (with the start OFF of the set or `OFF_REF`; the intensity per scan without
  either). The rows above the map give the CW record's value and enhancement,
  and the largest cell with its rate.
- **Sets:** with `REPEATS` above 1, each cell is the mean over the sets; with
  "repeats" error bars it shows ± its standard error, with "noise floor" the
  combined σ.
- **Click** a cell to show its latest record on the spectrum side.
- **Exports:** "Export: Chirp EPS" writes `chirp2d.eps` (4.6 × 3.6 in, no
  latest-record outline). `values.tsv` adds `width_MHz`, `time_us`,
  `rate_MHz_per_us`, `ratio_to_cw`, and `cw_expno`; `records.csv` adds the first
  three.

### OFF reference in the viewer

For a run with `# off_ref`, the "OFF ref" row gives the reference's value; its
OFF records, if any, are listed as a multiple of it, and the y label names it.
If the folder is not where `run.txt` says (a copied data directory), a dataset
of the same name next to the run's dataset is used. A reference that cannot be
read is reported, and the start OFF of each set is used instead.

### Error bars

"Error bars" in the top bar adds error bars to the profile or the build-up, in
the window, `plot.png`, the EPS export, `values.tsv`, and `records.csv`. With
error bars off, everything is as before.

- **noise floor**: ±1σ of each record from the noise of its own spectrum. By
  default the noise is measured on the points outside the intensity window,
  with peaks (spinning sidebands, other lines) and a smooth baseline left out;
  a signal-free range can be typed instead in the row that appears below the
  top bar ("noise from … to … ppm"; shaded grey in the spectrum). The σ of
  `sum` and of the window integral includes the correlation between
  neighbouring points (zero filling, apodization). For `extreme` and `max` it
  is the noise of one point, which is an upper bound: the maximum of a
  well-digitized peak top scatters somewhat less. For `FID(t0)` it comes from
  the noise in the last quarter of the fid. For I_on/I_off − 1 the σ of the
  start OFF is included. The spectrum pane shows the σ of the record shown.
- **repeats**: the mean of the records at the same frequency (profile) or D1
  (build-up, ON and OFF separately), over the sets of a run with `REPEATS` > 1
  or a D1 that appears more than once, or of the k-th record of each set
  (decay), ± its standard error. The sets are then
  shown as one series. A point measured once has no bar.
- For build-ups and decays, "weight the fits by 1/σ²" (in the same row) fits with these
  errors instead of NS and takes the parameter errors from them; the fit row
  then shows χ²/dof, which is about 1 when the noise explains the scatter, and
  a note when the scatter is clearly larger. With repeats, this needs at least
  3 records at every D1 (the standard error of 2 records is too rough to weight
  by); otherwise the fit stays weighted by NS and says so.

## Phasing the TopSpin data after a run

Set the phase in the viewer and press "Apply to all records"; this writes
`phase.txt` in the run folder. Then, with no acquisition running, type
`fs_rephase` in TopSpin and choose the run's `run.txt`. The script measures
TopSpin's phase convention on the first record, checks that it reproduces the
viewer's phase, asks for confirmation, and reprocesses every record with the
new PHC0 and PHC1. Everything is logged in `rephase.log` in the run folder.
This works for build-up and decay runs as well.
