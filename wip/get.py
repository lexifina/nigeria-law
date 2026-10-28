"""Fetch one URL through the shared adapter's cache (rate-limited, logged): python -X utf8 get.py URL [out]."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "africa-law"))
import peachjam  # noqa: E402

DELAYS = {"pre.cac.gov.ng": 1.0, "ncc.gov.ng": 1.0, "www.ncc.gov.ng": 1.0, "aserc.anambrastate.gov.ng": 1.0, "nass.gov.ng": 1.0, "www.nass.gov.ng": 1.0, "placng.org": 1.0, "www.placng.org": 1.0,
          "justice.gov.ng": 1.0, "www.justice.gov.ng": 1.0, "ndpc.gov.ng": 1.0, "www.ndpc.gov.ng": 1.0,
          "cac.gov.ng": 1.0, "www.cac.gov.ng": 1.0}
peachjam.CRAWL_DELAY.update(DELAYS)
c = peachjam.Cache(HERE)
b = c.get(sys.argv[1])
print(len(b), c.path(sys.argv[1]).name)
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_bytes(b)
