import os
import subprocess
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import dotenvx_runtime

CLI = Path(__file__).resolve().parents[2] / "src" / "cli" / "dotenvx.js"


def test_node_encrypt_python_decrypt():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=shhh\n")

        subprocess.run([
            "node",
            str(CLI),
            "encrypt"
        ], cwd=tmp, check=True)

        content = env_file.read_text()
        assert "SECRET=encrypted:" in content

        result = dotenvx_runtime.load(str(env_file))
        assert result["SECRET"] == "shhh"
        assert os.environ["SECRET"] == "shhh"
        assert not any(v.startswith("encrypted:") for v in result.values())
