# Workbench tools

Tools for reviewing the DNP runs on a copy of the data (on fbml-rsp, in
`D:\workbench\dnp800`), not on the spectrometer. They only read the data; the
review tools write `review.txt` files next to `run.txt` and never change `run.txt`
or the TopSpin data.

| Tool | What it does |
|---|---|
| `dnp_catalog.py` | One table of every run (`catalog.csv`, `catalog.html`): type, date, dataset, expnos, status, sample, rotor, MAS, temperature, result, and flags for anything to check |

## The catalog

```bat
cd D:\workbench\dnp800
.venv\Scripts\python code\workbench\dnp_catalog.py raw\wiesnern ^
    --runlog raw\_meta\dnp-run-log.txt --index raw\_meta\fs_runs.tsv --out catalog
```

then open `catalog\catalog.html`. It also runs on the spectrometer PC (Python 3.6, no
extra packages): `python3 dnp_catalog.py /opt/nmrdata/wiesnern --out ~/catalog`.

Rotor, MAS rate and temperature are read from the free-text conditions of `run.txt`
(`13 kHz MAS, 1.3 mm (c-1-3) Diamond rotor, RT`). Where they disagree, the catalog
uses `review.txt` first, then the hand-written run log, then `run.txt`, and shows a
cell in orange with what `run.txt` says. The flags column lists what to check:
`run.txt edited` / `settings.txt edited` (modified after the run), `title differs`
(the TopSpin title disagrees with `run.txt`), `log differs`, `unknown rotor`
(not in `--rotors`, default `c-1-1,c-1-3,a-5-1,zirconia`), `not in log`, `stopped`,
`no records`. Runs in `fs_runs.tsv` without a folder are listed as `no folder`
(hidden by default in the page).

## review.txt

One per run folder, `key = value` lines:

```
status = approved          # approved | discarded | unreviewed
reason =                   # why, for discarded
rotor = c-1-3
mas_khz = 13
temp = RT                  # RT or e.g. 100 K
sample = Diamond P1 center
notes = free text
reviewer = Ravi
date = 2026-11-22
```

Values given here override what `run.txt` says, in the catalog and (later) in the
viewer and the figure tool.
