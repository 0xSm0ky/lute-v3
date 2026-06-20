#!/usr/bin/env bash
#
# Lute free cloud backup — one-off, manual.
# Usage:   bash /root/lute-v3/backup.sh
#
# Makes a consistent, compressed (optionally encrypted) snapshot of the Lute
# database + user media and uploads it to a free cloud provider via rclone.
#
# One-time setup before first run:
#   1. rclone config        -> create a remote named exactly "lutecloud"
#                              (Google Drive 15GB / Mega 20GB / Dropbox 2GB, all free)
#   2. (optional) export LUTE_BACKUP_PASSPHRASE="something-strong"
#                              to encrypt backups with gpg before upload.

set -euo pipefail

# ---- config ----------------------------------------------------------------
DATA_DIR="/root/lute-v3/lute_data"      # active Lute data dir
REMOTE="lutecloud:lute-backups"         # rclone remote:path
KEEP=14                                 # how many archives to retain remotely
# ----------------------------------------------------------------------------

DB="$DATA_DIR/lute.db"
STAMP="$(date +%Y%m%d-%H%M%S)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

[ -f "$DB" ] || { echo "ERROR: database not found at $DB" >&2; exit 1; }
command -v rclone >/dev/null || { echo "ERROR: rclone not installed" >&2; exit 1; }

echo ">> Making consistent copy of lute.db ..."
# Use SQLite's online backup API (safe while Lute is running) via Python.
python3 -c "import sqlite3,sys
s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2])
s.backup(d); d.close(); s.close()" "$DB" "$TMP/lute.db"

echo ">> Bundling db + media into archive ..."
ARCHIVE="$TMP/lute-backup-$STAMP.tar.gz"
# Safe db copy goes in as-is; media dirs copied from the live tree.
# Local-only stuff (*.bak, .system_db_backups, temp) is intentionally excluded.
tar czf "$ARCHIVE" -C "$TMP" lute.db \
    -C "$DATA_DIR" useraudio userimages userthemes

UPLOAD="$ARCHIVE"
if [ -n "${LUTE_BACKUP_PASSPHRASE:-}" ]; then
    echo ">> Encrypting with gpg ..."
    gpg --batch --yes --passphrase "$LUTE_BACKUP_PASSPHRASE" \
        -c -o "$ARCHIVE.gpg" "$ARCHIVE"
    UPLOAD="$ARCHIVE.gpg"
fi

echo ">> Uploading $(basename "$UPLOAD") ($(du -h "$UPLOAD" | cut -f1)) to $REMOTE ..."
rclone copy "$UPLOAD" "$REMOTE/" --progress

echo ">> Pruning remote to newest $KEEP archives ..."
# List remote files newest-first, skip the first $KEEP, delete the rest.
rclone lsf "$REMOTE/" 2>/dev/null | sort -r | tail -n +$((KEEP + 1)) | \
while read -r old; do
    [ -n "$old" ] && echo "   deleting old: $old" && rclone deletefile "$REMOTE/$old"
done

echo ">> Done. Backup uploaded as $(basename "$UPLOAD")"
