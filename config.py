"""Shared constants and paths for the pipeline."""

# Feed cut-off sequence, measured 2026-09-18 when the replication feed
# returned 3,409 results instead of the requested 10,000.
SNAPSHOT_SEQ = 131_412_017
SNAPSHOT_DATE = "2026-09-18"

# --- data directories -------------------------------------------------
# Kept under their original names because they already hold data; renaming
# would mean moving ~2 GB and re-syncing every machine. Centralised here so
# a future rename touches one file.
DIR_INDEX    = "data/pasada1"      # pass 01 output: id, seq, deleted
DIR_DEPS     = "data/pasada2"      # pass 02 output: prod/dev dependencies
DIR_PROFILE  = "data/profile"      # pass 04 output
DIR_DOWNLOAD = "data/downloads"    # pass 05 output

# --- single name cache, shared by every pass that needs it ------------
NAMES_CACHE = "data/names_sorted.json"


USER_AGENT = "UCN-research/1.0 (+https://github.com/yojair0/Ecosistema-npm)"
