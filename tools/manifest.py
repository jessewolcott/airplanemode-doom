"""Write wads/manifest.json: the size of every file the page downloads before a game starts
(so the progress bar is right even when the server sends them gzipped)."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
files = sorted(list((root / "wads").glob("*.wad")) + list((root / "engine").glob("*.wasm")))
sizes = {str(p.relative_to(root)).replace("\\", "/"): p.stat().st_size for p in files}
(root / "wads" / "manifest.json").write_text(json.dumps(sizes, indent=1))
print(json.dumps(sizes, indent=1))
