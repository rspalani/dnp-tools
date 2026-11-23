#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dnp_catalog.py  -  one table of every DNP run, for review (Python 3.6+, standard library only)

    python dnp_catalog.py ROOT [ROOT ...] [--runlog dnp-run-log.txt] [--index fs_runs.tsv]
                          [--out CATALOG_DIR] [--rotors c-1-1,c-1-3,a-5-1,zirconia]

ROOT is a folder of datasets (e.g. D:\\workbench\\dnp800\\raw\\wiesnern, or
/opt/nmrdata/wiesnern); every <ROOT>/<dataset>/fs_runs/<run>/run.txt is a run. Nothing
under ROOT is changed: the script only reads. It writes, in --out:

    catalog.csv    one row per run (see COLUMNS)
    catalog.html   the same table, filterable, with the flags highlighted

What is read for each run:
  run.txt           type, status (complete / stopped / no end line), records, sample,
                    conditions (rotor, MAS rate, temperature are parsed from that text)
  settings.txt      SAMPLE and MAS_INFO as the run started
  log.txt           its time, to tell whether run.txt was changed after the run
  values.tsv        the viewer's last result: the fitted T_B / T_1 of build-ups and decays,
                    the largest |y| of a profile or power dependence, the best chirp
  <dataset>/<first expno>/pdata/1/title   the TopSpin title written when the run started
  review.txt        the reviewer's decisions (written by the review tools, never by an
                    acquisition): status = approved | discarded | unreviewed, and
                    corrections (rotor, mas_khz, temp, sample, notes). Corrections win over
                    what run.txt says; run.txt itself is never changed.
  --runlog          the hand-written run log (dnp-run-log.txt); for every run id in it,
                    the rotor / MAS / temperature of the nearest conditions line above it
                    in the same dated section. Shown as 'log_*' columns and compared.
  --index           fs_runs.tsv; runs that appear there but have no folder are listed
                    at the end of the table (status 'no folder').

Flags (column 'flags', ';'-separated):
  run.txt edited       run.txt was modified more than 2 min after log.txt (the end of the run)
  settings.txt edited  settings.txt was modified more than 5 min after the run started
  title differs        rotor / MAS / temperature in the TopSpin title differ from run.txt
  log differs          ... in the run log differ from run.txt (the log is taken as correct)
  unknown rotor        the rotor is not in --rotors
  no rotor / no MAS / no temp   not given in the conditions
  stopped / no records / not in log
"""
import argparse
import csv
import datetime
import html
import io
import os
import re
import sys
import time

KNOWN_ROTORS = "c-1-1,c-1-3,a-5-1,zirconia"
RUN_ID_RE = re.compile(r"(\d{8}-\d{6})_([A-Za-z0-9_-]+?)_e(\d+)")
ROTOR_RE = re.compile(r"\b([a-z])-(\d+)-(\d+)\b", re.I)
MAS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*kHz", re.I)
TEMP_K_RE = re.compile(r"(\d+(?:\.\d+)?)\s*K\b")
TYPES = ("fs", "buildup", "decay", "powdep", "chirp2d")
TYPE_SHORT = {"fs": "fs", "buildup": "bu", "decay": "decay", "powdep": "powdep", "chirp2d": "chirp2d"}

COLUMNS = ["status", "review", "type", "run_id", "date", "dataset", "expnos", "records",
           "sample", "rotor", "mas_khz", "temp", "freq_GHz", "result",
           "rotor_runtxt", "mas_runtxt", "temp_runtxt", "rotor_title", "rotor_settings",
           "rotor_log", "mas_log", "temp_log", "flags", "conditions_runtxt", "log_line",
           "end", "notes", "folder"]


# ---------------------------------------------------------------------------- parsing
def parse_conditions(text):
    """(rotor, mas_khz, temp) from free text such as
    '13 kHz MAS, 1.3 mm (c-1-3) Diamond rotor, RT' or '1.3mm zirconia rotor, 100 K'."""
    text = text or ""
    rotor = ""
    m = ROTOR_RE.search(text)
    if m:
        rotor = "%s-%s-%s" % (m.group(1).lower(), m.group(2), m.group(3))
    elif re.search(r"zirconia", text, re.I):
        rotor = "zirconia"
    mas = ""
    m = MAS_RE.search(text)
    if m:
        mas = ("%g" % float(m.group(1)))
    temp = ""
    m = TEMP_K_RE.search(text)
    if m:
        temp = "%g K" % float(m.group(1))
    elif re.search(r"(?<![A-Za-z])RT(?:\b|(?=expt))|room\s*temp", text, re.I):
        temp = "RT"
    return rotor, mas, temp


def read_text(path):
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (IOError, OSError):
        return None


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def parse_time(s):
    try:
        return datetime.datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def read_run(path):
    """Header (dict), data rows (lists of fields), end line text or None."""
    meta, rows, end = {}, [], None
    text = read_text(path) or ""
    for line in text.splitlines():
        if line.startswith("#"):
            m = re.match(r"#\s*([A-Za-z_0-9]+)\s*=\s*(.*)$", line)
            if m and m.group(1) not in meta:
                meta[m.group(1)] = m.group(2).strip()
            m = re.match(r"#\s*end:\s*(.*)$", line)
            if m:
                end = m.group(1).strip()
        elif line.strip():
            rows.append(line.rstrip("\n").split("\t"))
    return meta, rows, end


def read_settings(path):
    out = {}
    for line in (read_text(path) or "").splitlines():
        m = re.match(r"^([A-Z_0-9]+)\s*=\s*(.*)$", line)
        if m:
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            out[m.group(1)] = v
    return out


def read_review(path):
    """review.txt: 'key = value' lines; '#' starts a comment."""
    out = {}
    for line in (read_text(path) or "").splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_]+)\s*=\s*(.*)$", line)
        if m:
            out[m.group(1).lower()] = m.group(2).strip()
    return out


def values_result(path, rtype):
    """A short result from the viewer's values.tsv, or ''."""
    text = read_text(path)
    if not text:
        return ""
    head = [l[1:].strip() for l in text.splitlines() if l.startswith("#")]
    lines = [l for l in text.splitlines() if l and not l.startswith("#")]
    if rtype in ("buildup", "decay"):
        out = []
        for h in head:
            if not re.search(r"\bT_(?:B|1)\s+[\d.]", h) or h.startswith("fit"):
                if re.match(r"^[^:]{1,40}:\s*no fit:", h):
                    out.append(h)
                continue
            name = h.split(":", 1)[0].strip()
            ts = ["%s %s" % (k, v.strip()) for k, v in re.findall(r"\b(T_B|T_1|T_2)\s+([\d.][^;]*)", h)]
            out.append("%s: %s%s" % (name, ", ".join(ts), " (not determined)" if "not determined" in h else ""))
        return "; ".join(out)
    if rtype == "powdep":
        fits = [h for h in head if h.startswith("fit ") or re.match(r"^fit\s+\S+:", h)]
        if fits:
            return "; ".join(f[4:] if f.startswith("fit ") else f for f in fits)[:200]
    if not lines:
        return ""
    cols = lines[0].split("\t")
    key = "ratio_to_cw" if (rtype == "chirp2d" and "ratio_to_cw" in cols) else ("y" if "y" in cols else None)
    if key is None:
        return ""
    k = cols.index(key)
    fcol = cols.index("freq_GHz") if "freq_GHz" in cols else None
    best = None
    wcol = cols.index("width_MHz") if "width_MHz" in cols else None
    for l in lines[1:]:
        f = l.split("\t")
        if wcol is not None and len(f) > wcol and f[wcol] in ("0", "0.0", ""):
            continue                      # the CW reference of a chirp grid
        try:
            v = float(f[k])
        except (ValueError, IndexError):
            continue
        if best is None or abs(v) > abs(best[0]):
            best = (v, f)
    if best is None:
        return ""
    v, f = best
    if rtype == "chirp2d":
        w = f[cols.index("width_MHz")] if "width_MHz" in cols else "?"
        t = f[cols.index("time_us")] if "time_us" in cols else "?"
        return "best chirp/CW %.3g (%s MHz, %s us)" % (v, w, t)
    where = (" at %s GHz" % f[fcol]) if (fcol is not None and rtype == "fs") else ""
    return "largest |%s| %.4g%s" % (key, v, where)


def topspin_title(dataset_dir, expno):
    if not expno:
        return ""
    t = read_text(os.path.join(dataset_dir, str(expno), "pdata", "1", "title"))
    return (t or "").strip().splitlines()[0] if t and t.strip() else ""


# ---------------------------------------------------------------------------- run log
def parse_runlog(path):
    """{run_id: (rotor, mas, temp, the conditions line)} from the free-form run log.
    Entries are taken only after the first dated section ('---261118:' or '261109-now:'),
    so the TO DO list at the top is ignored. Within a section, a run id gets the most recent
    line above it that names a rotor, MAS rate or temperature."""
    text = read_text(path)
    out = {}
    if not text:
        return out
    started = False
    ctx = ("", "", "", "")
    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^-{2,}\s*\d{6}", line) or re.match(r"^\d{6}(-\S*)?:", line):
            started = True
            ctx = ("", "", "", "")
            continue
        if not started or not line:
            continue
        ids = list(RUN_ID_RE.finditer(line))
        if not ids:
            # a run id with its leading '2' lost ('0261115-162231_bu_...')
            m = re.search(r"(?<!\d)(\d{7}-\d{6}_[A-Za-z0-9_-]+?_e\d+)", line)
            if m and m.group(1).startswith("0"):
                ids = [RUN_ID_RE.search("2" + m.group(1))]
        if ids:
            for m in ids:
                rid = m.group(0)
                if rid not in out and ctx[3]:
                    out[rid] = ctx
            continue
        r, mas, t = parse_conditions(line)
        if r or mas or t:
            # keep what this line does not say from the line before (same section)
            ctx = (r or ctx[0], mas or ctx[1], t or ctx[2], line)
    return out


# ---------------------------------------------------------------------------- catalog
def scan(roots):
    for root in roots:
        if not os.path.isdir(root):
            print("not a folder: %s" % root, file=sys.stderr)
            continue
        for ds in sorted(os.listdir(root)):
            for sub in ("fs_runs", "dnp_runs"):
                rd = os.path.join(root, ds, sub)
                if not os.path.isdir(rd):
                    continue
                for run in sorted(os.listdir(rd)):
                    if os.path.isfile(os.path.join(rd, run, "run.txt")):
                        yield os.path.join(root, ds), ds, os.path.join(rd, run)


def catalog_row(dataset_dir, dataset, folder, runlog, known):
    run_path = os.path.join(folder, "run.txt")
    meta, rows, end = read_run(run_path)
    rtype = meta.get("type", "fs")
    run_id = meta.get("run_id") or os.path.basename(folder)
    settings = read_settings(os.path.join(folder, "settings.txt"))
    review = read_review(os.path.join(folder, "review.txt"))
    started = parse_time(meta.get("started", ""))
    flags = []

    cond = meta.get("conditions", "")
    r_rt, m_rt, t_rt = parse_conditions(cond)
    first = rows[0][0] if rows and rows[0] else ""
    last = rows[-1][0] if rows and rows[-1] else ""
    title = topspin_title(dataset_dir, first)
    r_ti, m_ti, t_ti = parse_conditions(title)
    r_se, m_se, t_se = parse_conditions(settings.get("MAS_INFO", ""))
    lg = runlog.get(run_id)
    r_lg, m_lg, t_lg, l_lg = lg if lg else ("", "", "", "")

    # status of the acquisition
    if end is None:
        status = "no end line"
    elif end.startswith("complete"):
        status = "complete"
    else:
        status = "stopped"
        flags.append("stopped")
    if not rows:
        flags.append("no records")

    # edits after the fact
    t_run, t_log, t_set = (mtime(os.path.join(folder, n)) for n in ("run.txt", "log.txt", "settings.txt"))
    if t_run and t_log and t_run - t_log > 120:
        flags.append("run.txt edited %s" % datetime.datetime.fromtimestamp(t_run).strftime("%Y-%m-%d %H:%M"))
    if t_set and started and t_set - time.mktime(started.timetuple()) > 300:
        flags.append("settings.txt edited %s" % datetime.datetime.fromtimestamp(t_set).strftime("%Y-%m-%d %H:%M"))

    def differ(a, b):
        return [n for n, x, y in zip(("rotor", "MAS", "temp"), a, b) if x and y and x != y]

    d = differ((r_rt, m_rt, t_rt), (r_ti, m_ti, t_ti))
    if d:
        flags.append("title differs (%s)" % ", ".join(d))
    if lg:
        d = differ((r_rt, m_rt, t_rt), (r_lg, m_lg, t_lg))
        if d:
            flags.append("log differs (%s)" % ", ".join(d))
    elif rows:
        flags.append("not in log")

    # effective values: review.txt > run log > run.txt
    rotor = review.get("rotor") or r_lg or r_rt
    mas = review.get("mas_khz") or m_lg or m_rt
    temp = review.get("temp") or t_lg or t_rt
    if rotor and rotor.lower() not in known:
        flags.append("unknown rotor %s" % rotor)
    if not rotor:
        flags.append("no rotor")
    if not mas:
        flags.append("no MAS")
    if not temp:
        flags.append("no temp")

    freq = meta.get("freq_GHz", "")
    if rtype == "fs" and rows:
        fr = [float(r[3]) for r in rows if len(r) > 3 and re.match(r"^\d", r[3])]
        if fr:
            freq = "%.3f-%.3f" % (min(fr), max(fr))
    if freq == "-" and meta.get("set_cw"):
        freq = ",".join(p.split()[1] for p in meta["set_cw"].split(";") if len(p.split()) > 1)

    return {
        "status": status,
        "review": review.get("status", "unreviewed"),
        "type": TYPE_SHORT.get(rtype, rtype),
        "run_id": run_id,
        "date": started.strftime("%Y-%m-%d %H:%M") if started else "",
        "dataset": dataset,
        "expnos": ("%s-%s" % (first, last)) if first else "",
        "records": str(len(rows)),
        "sample": review.get("sample") or meta.get("sample", ""),
        "rotor": rotor, "mas_khz": mas, "temp": temp, "freq_GHz": freq,
        "result": values_result(os.path.join(folder, "values.tsv"), rtype),
        "rotor_runtxt": r_rt, "mas_runtxt": m_rt, "temp_runtxt": t_rt,
        "rotor_title": r_ti, "rotor_settings": r_se,
        "rotor_log": r_lg, "mas_log": m_lg, "temp_log": t_lg,
        "flags": "; ".join(flags),
        "conditions_runtxt": cond, "log_line": l_lg,
        "end": end or "", "notes": review.get("notes", ""),
        "folder": folder,
    }


def index_without_folder(index_path, seen):
    rows = []
    text = read_text(index_path) if index_path else None
    if not text:
        return rows
    starts = {}
    ends = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        if len(f) < 9:
            continue
        (starts if f[1] == "start" else ends)[f[3]] = f
    for rid, f in sorted(starts.items()):
        if rid in seen:
            continue
        e = ends.get(rid)
        m = RUN_ID_RE.match(rid)
        lab = m.group(2) if m else ""
        typ = "fs"
        for t in ("bu", "decay", "powdep", "chirp2d"):
            if lab.startswith(t + "_") or lab == t:
                typ = t
        rows.append({c: "" for c in COLUMNS})
        rows[-1].update({"status": "no folder", "review": "", "type": typ, "run_id": rid,
                         "date": f[0][:16], "dataset": os.path.basename(f[6]), "expnos": f[7],
                         "sample": f[5], "end": e[2] if e else "", "folder": f[8],
                         "flags": "in index only"})
    return rows


# ---------------------------------------------------------------------------- output
HTML_HEAD = """<!doctype html><html><head><meta charset="utf-8"><title>DNP run catalog</title>
<style>
body{font:13px/1.35 system-ui,Segoe UI,Arial,sans-serif;margin:12px;color:#111;background:#fff}
h1{font-size:18px;margin:0 0 6px} .bar{margin:6px 0 10px} .bar input,.bar select{font:inherit;margin-right:8px}
.wrap{overflow-x:auto} table{border-collapse:collapse} th,td{border-bottom:1px solid #ddd;padding:3px 6px;text-align:left;vertical-align:top;white-space:nowrap}
th{position:sticky;top:0;background:#f3f3f3;cursor:pointer} td.flags{white-space:normal;max-width:360px;color:#a40}
td.result,td.fq{max-width:260px;overflow:hidden;text-overflow:ellipsis} td.flags{max-width:320px} tr.approved td.st{color:#070;font-weight:600} tr.discarded{color:#999}
tr.discarded td.flags{color:#c99} .bad{background:#fff3e0} .small{color:#666;font-size:12px}
</style></head><body>
<h1>DNP run catalog</h1><div class="small">%s</div>
<div class="bar">Search <input id="q" size="30" placeholder="text in any column">
Type <select id="ty"><option value="">all</option>%s</select>
Review <select id="rv"><option value="">all</option><option>unreviewed</option><option>approved</option><option>discarded</option></select>
<label><input type="checkbox" id="fl"> only flagged</label>
<label><input type="checkbox" id="hd" checked> hide 'no folder'</label> <span id="n"></span></div>
<div class="wrap"><table id="t"><thead><tr>%s</tr></thead><tbody>
"""
HTML_TAIL = """</tbody></table></div>
<script>
var q=document.getElementById('q'),ty=document.getElementById('ty'),rv=document.getElementById('rv'),
fl=document.getElementById('fl'),hd=document.getElementById('hd'),rows=[].slice.call(document.querySelectorAll('#t tbody tr'));
function f(){var s=q.value.toLowerCase(),n=0;rows.forEach(function(r){var ok=(!s||r.textContent.toLowerCase().indexOf(s)>=0)
&&(!ty.value||r.dataset.type==ty.value)&&(!rv.value||r.dataset.review==rv.value)&&(!fl.checked||r.dataset.flag=='1')
&&(!hd.checked||r.dataset.status!='no folder');r.style.display=ok?'':'none';if(ok)n++});document.getElementById('n').textContent=n+' runs'}
[q,ty,rv,fl,hd].forEach(function(e){e.addEventListener('input',f);e.addEventListener('change',f)});f();
document.querySelectorAll('#t th').forEach(function(th,i){th.addEventListener('click',function(){var b=document.querySelector('#t tbody'),
asc=th.dataset.asc!='1';th.dataset.asc=asc?'1':'0';rows.sort(function(x,y){var a=x.children[i].textContent,c=y.children[i].textContent;
return (a<c?-1:a>c?1:0)*(asc?1:-1)});rows.forEach(function(r){b.appendChild(r)})})});
</script></body></html>
"""
SHOWN = ["review", "run_id", "type", "date", "dataset", "expnos", "records", "status", "rotor",
         "mas_khz", "temp", "sample", "freq_GHz", "result", "flags"]


def write_outputs(rows, out_dir, sources):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with io.open(os.path.join(out_dir, "catalog.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    e = html.escape
    types = "".join("<option>%s</option>" % t for t in sorted(set(r["type"] for r in rows if r["type"])))
    with io.open(os.path.join(out_dir, "catalog.html"), "w", encoding="utf-8") as fh:
        fh.write(HTML_HEAD % (e(sources), types, "".join("<th>%s</th>" % e(c) for c in SHOWN)))
        for r in rows:
            fh.write('<tr class="%s" data-type="%s" data-review="%s" data-status="%s" data-flag="%s">'
                     % (e(r["review"]), e(r["type"]), e(r["review"]), e(r["status"]), "1" if r["flags"] else "0"))
            for c in SHOWN:
                v = r[c]
                cls = {"review": "st", "flags": "flags", "result": "result", "freq_GHz": "fq"}.get(c, "")
                if c in ("rotor", "mas_khz", "temp") and r.get(c) and (
                        (c == "rotor" and r["rotor_runtxt"] and r["rotor_runtxt"] != r["rotor"]) or
                        (c == "mas_khz" and r["mas_runtxt"] and r["mas_runtxt"] != r["mas_khz"]) or
                        (c == "temp" and r["temp_runtxt"] and r["temp_runtxt"] != r["temp"])):
                    cls += " bad"
                    v = "%s (run.txt: %s)" % (v, {"rotor": r["rotor_runtxt"], "mas_khz": r["mas_runtxt"],
                                                 "temp": r["temp_runtxt"]}[c])
                if c == "run_id":
                    v = '<a href="file:///%s">%s</a>' % (e(r["folder"].replace("\\", "/").lstrip("/")), e(v))
                    fh.write('<td class="%s">%s</td>' % (cls, v))
                else:
                    fh.write('<td class="%s" title="%s">%s</td>' % (cls, e(v), e(v)))
            fh.write("</tr>\n")
        fh.write(HTML_TAIL)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("roots", nargs="+", help="folders of datasets, e.g. raw\\wiesnern")
    ap.add_argument("--runlog", help="dnp-run-log.txt")
    ap.add_argument("--index", help="fs_runs.tsv")
    ap.add_argument("--out", default="catalog", help="output folder (default: ./catalog)")
    ap.add_argument("--rotors", default=KNOWN_ROTORS, help="known rotors, comma-separated")
    a = ap.parse_args(argv)
    known = set(x.strip().lower() for x in a.rotors.split(",") if x.strip())
    runlog = parse_runlog(a.runlog) if a.runlog else {}
    rows = [catalog_row(dd, ds, f, runlog, known) for dd, ds, f in scan(a.roots)]
    rows.sort(key=lambda r: r["date"], reverse=True)
    seen = set(r["run_id"] for r in rows)
    rows += index_without_folder(a.index, seen)
    missing = sorted(set(runlog) - seen)
    src = "%d runs from %s; run log: %s (%d run ids%s); written %s" % (
        len(seen), ", ".join(a.roots), a.runlog or "none", len(runlog),
        ("; in the log but not found: " + ", ".join(missing)) if missing else "",
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    write_outputs(rows, a.out, src)
    nflag = sum(1 for r in rows if r["flags"] and r["status"] != "no folder")
    print(src)
    print("%d runs flagged; wrote %s" % (nflag, os.path.join(a.out, "catalog.html")))


if __name__ == "__main__":
    main()
