import sys
from pathlib import Path

# Add project root so "src" resolves to linear_programming/src.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
