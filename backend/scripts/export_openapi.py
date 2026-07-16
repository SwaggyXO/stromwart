"""Export the Stromwart OpenAPI schema without starting the server."""
import json
import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
os.chdir(backend_root)
sys.path.insert(0, str(backend_root / "src"))

from stromwart.app import create_app  # noqa: E402

app = create_app()
schema = app.openapi()

output = Path(__file__).parents[2] / "docs" / "openapi.json"
output.write_text(json.dumps(schema, indent=2))
print(f"Schema written to {output} ({len(schema['paths'])} endpoints)")
