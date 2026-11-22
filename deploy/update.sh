#!/bin/bash
# update.sh - install or update the DNP tools on the spectrometer PC from GitHub.
#
#   bash /home/nmrsu/src/dnp-tools/deploy/update.sh            update to the latest main
#   bash /home/nmrsu/src/dnp-tools/deploy/update.sh --dry-run  show what would change, change nothing
#   bash /home/nmrsu/src/dnp-tools/deploy/update.sh --force    update even if a run seems to be in progress
#
# Run it as nmrsu (it asks for the sudo password to write in /opt). It:
#   1. pulls the latest main into the clone (fast-forward only; local edits stop it),
#   2. refuses to go on while a run is in progress (from the run index),
#   3. copies the programs to /opt/dnptools and the TopSpin commands to TopSpin,
#      keeping each replaced file in /opt/dnptools/backup/<date>/,
#   4. never overwrites the site files: awg_cmd.py (AWG address), awg_power_cal.txt,
#      and the settings files in /opt/nmrdata/fs_settings (new ones are added),
#   5. writes /opt/dnptools/VERSION, which every new run copies into run.txt.
# The paths can be changed with environment variables (for testing).

set -u
REPO="${DNP_REPO:-/home/nmrsu/src/dnp-tools}"
OPT="${DNP_OPT:-/opt/dnptools}"
TOPSPIN_USER="${DNP_TOPSPIN_USER:-/opt/topspin3.6.2/exp/stan/nmr/py/user}"
SETTINGS="${DNP_SETTINGS:-/opt/nmrdata/fs_settings}"
INDEX="${DNP_INDEX:-/opt/nmrdata/fs_runs.tsv}"
MONITOR="${DNP_MONITOR:-/opt/dnptools/dnp_monitor}"
SUDO="${DNP_SUDO-sudo}"
URL="https://github.com/rspalani/dnp-tools.git"
BRANCH=main

DRY=0; FORCE=0
for a in "$@"; do
    case "$a" in
        --dry-run) DRY=1 ;;
        --force)   FORCE=1 ;;
        -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
        *) echo "unknown option: $a"; exit 2 ;;
    esac
done

die() { echo "STOPPED: $*"; exit 1; }
command -v git >/dev/null || die "git is not installed (sudo zypper install git-core)"

# ---- 1. the clone ---------------------------------------------------------------
if [ ! -d "$REPO/.git" ]; then
    if [ -e "$REPO" ]; then
        old="$REPO.before-git-$(date +%Y%m%d-%H%M%S)"
        echo "$REPO exists but is not a git clone (an unpacked tarball); moving it to $old"
        [ $DRY -eq 1 ] || mv "$REPO" "$old" || die "could not move $REPO"
    fi
    echo "cloning $URL into $REPO"
    [ $DRY -eq 1 ] && { echo "(dry run: stopping here; nothing to compare yet)"; exit 0; }
    mkdir -p "$(dirname "$REPO")" && git clone -q -b "$BRANCH" "$URL" "$REPO" || die "git clone failed"
else
    cd "$REPO" || die "cannot enter $REPO"
    [ -z "$(git status --porcelain --untracked-files=no)" ] || {
        git status --short --untracked-files=no
        die "files in $REPO were edited by hand (listed above). Copy anything you need, then: git -C $REPO checkout -- ."; }
    git fetch -q origin "$BRANCH" || die "git fetch failed (network?)"
    new=$(git rev-list --count HEAD..origin/$BRANCH)
    if [ "$new" -gt 0 ]; then
        echo "$new new commit(s) on GitHub:"
        git log --oneline --no-decorate HEAD..origin/$BRANCH | sed 's/^/    /'
    else
        echo "the clone is already at the latest $BRANCH"
    fi
    if [ $DRY -eq 0 ]; then
        git checkout -q "$BRANCH" && git merge -q --ff-only "origin/$BRANCH" || die "could not fast-forward to origin/$BRANCH"
    fi
fi
cd "$REPO" || die "cannot enter $REPO"
SRC="$REPO/frequency_profile"
if [ $DRY -eq 1 ]; then
    # compare against what is on GitHub without touching the clone
    TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
    git archive "origin/$BRANCH" | tar -x -C "$TMP"
    SRC="$TMP/frequency_profile"; MON_SRC="$TMP"
    COMMIT=$(git rev-parse --short origin/$BRANCH); CDATE=$(git log -1 --format=%cd --date=short origin/$BRANCH)
else
    MON_SRC="$REPO"
    COMMIT=$(git rev-parse --short HEAD); CDATE=$(git log -1 --format=%cd --date=short HEAD)
fi

# ---- 2. no update during a run ------------------------------------------------------
# A run writes 'start' to the index when it begins and 'end' when it ends; a run_id
# with a start and no end in the last 200 lines is taken as running.
if [ -r "$INDEX" ]; then
    running=$(tail -n 200 "$INDEX" | awk -F'\t' '$1 !~ /^#/ {if ($2=="start") s[$4]=$1; else if ($2=="end") delete s[$4]}
                                              END {for (r in s) print "    " r " (started " s[r] ")"}')
    if [ -n "$running" ]; then
        echo "These runs have started and not ended (or ended without writing to the index):"
        echo "$running"
        if [ $FORCE -eq 0 ] && [ $DRY -eq 0 ]; then
            die "update after the run, or with --force if none is really running"
        fi
    fi
fi

# ---- 3./4. install ------------------------------------------------------------------
BACKUP="$OPT/backup/$(date +%Y%m%d-%H%M%S)"
changed=0
install_file() {   # install_file SRC DEST_DIR [keep]   keep: never overwrite an existing file
    local src="$1" dir="$2" keep="${3:-}" dest="$2/$(basename "$1")"
    if [ -e "$dest" ] && cmp -s "$src" "$dest"; then return; fi
    if [ -e "$dest" ] && [ "$keep" = keep ]; then
        echo "  kept (site file): $dest"; return
    fi
    changed=$((changed + 1))
    if [ -e "$dest" ]; then echo "  update: $dest"; else echo "  new:    $dest"; fi
    [ $DRY -eq 1 ] && return
    if [ -e "$dest" ]; then
        $SUDO mkdir -p "$BACKUP" && $SUDO cp -p "$dest" "$BACKUP/" || die "could not back up $dest"
    fi
    $SUDO mkdir -p "$dir" && $SUDO cp "$src" "$dest" && $SUDO chmod a+r "$dest" || die "could not write $dest"
}

echo "installing $COMMIT ($CDATE):"
for f in fs_core.py fs_plot.py fs_rephase_core.py; do install_file "$SRC/dnptools/$f" "$OPT"; done
install_file "$SRC/dnptools/awg_cmd.py" "$OPT" keep
install_file "$SRC/dnptools/awg_power_cal.txt" "$OPT" keep
for f in "$SRC"/topspin/*.py; do install_file "$f" "$TOPSPIN_USER"; done
for f in "$SRC"/settings/*.py; do install_file "$f" "$SETTINGS" keep; done
mon_before=$changed
for f in dnp_monitor.py dnp_logviewer.py; do install_file "$MON_SRC/$f" "$MONITOR"; done
[ $changed -gt $mon_before ] && echo "  NOTE: the DNP monitor changed; close it and start it again (dnp_monitor)."
[ $DRY -eq 0 ] && [ -d "$SETTINGS" ] && $SUDO chown -R nmrsu "$SETTINGS" 2>/dev/null

# ---- 5. VERSION ---------------------------------------------------------------------
line="$COMMIT $CDATE (installed $(date '+%Y-%m-%d %H:%M'))"
if [ $DRY -eq 1 ]; then
    echo "$changed file(s) would change; VERSION would be: $line"
    exit 0
fi
echo "$line" | $SUDO tee "$OPT/VERSION" >/dev/null && $SUDO chmod a+r "$OPT/VERSION" || die "could not write $OPT/VERSION"
echo "$changed file(s) changed; $OPT/VERSION = $line"
[ $changed -gt 0 ] && [ -d "$BACKUP" ] && echo "replaced files kept in $BACKUP"
[ $changed -gt 0 ] && echo "A viewer that is open keeps the old code: close it and reopen it."
