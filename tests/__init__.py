"""Put the public package and this repository's rules on the path.

The public repository is expected beside this one (../nerodebench); set
NERODEBENCH_SRC to its src folder to use another checkout.
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("NERODEBENCH_SRC", HERE.parent / "nerodebench" / "src"))
for p in (str(SRC), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
