"""Step 1: pull IMF PortWatch daily chokepoint and Egyptian port data into data/raw/.

uv run python scripts/extract.py            # only missing or still-open years
uv run python scripts/extract.py --force    # re-download everything
"""

import argparse

from suez_portwatch.extract import extract

parser = argparse.ArgumentParser()
parser.add_argument("--force", action="store_true", help="re-download files that already exist")
extract(force=parser.parse_args().force)
