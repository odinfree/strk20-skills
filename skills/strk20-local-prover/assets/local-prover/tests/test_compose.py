"""Read-only integration checks; no daemon, image pull or credential required."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_check import check


class ComposeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("docker"):
            raise unittest.SkipTest("Docker CLI unavailable")
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, timeout=20)
        if result.returncode:
            raise unittest.SkipTest("Docker Compose plugin unavailable")

    def render(self, root, overrides=None):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("COMPOSE_", "PROVER_")) and key not in ("RPC_URL", "CHAIN_ID")}
        env.update(overrides or {})
        process = subprocess.run(
            ["docker", "compose", "--file", str(root / "compose.yaml"),
             "--env-file", str(root / ".env"), "config", "--format", "json"],
            cwd=root, env=env, capture_output=True, text=True, timeout=20, check=True)
        return json.loads(process.stdout)

    def test_explicit_files_ignore_foreign_compose_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copyfile(check.ROOT / "compose.yaml", root / "compose.yaml")
            (root / ".env").write_text("RPC_URL='https://example.invalid/intended'\n")
            (root / "foreign.env").write_text("RPC_URL='https://example.invalid/other'\n")
            for name in ("foreign.yaml", "compose.override.yaml"):
                (root / name).write_text("services:\n  unrelated:\n    image: example.invalid/unrelated\n")
            data = self.render(root, {"COMPOSE_FILE": str(root / "foreign.yaml"),
                                      "COMPOSE_ENV_FILES": str(root / "foreign.env")})
            self.assertEqual(set(data["services"]), {"prover"})
            self.assertEqual(data["services"]["prover"]["environment"]["RPC_URL"],
                             "https://example.invalid/intended")

    def test_supported_literals_match_checker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copyfile(check.ROOT / "compose.yaml", root / "compose.yaml")
            for url in ("https://example.invalid/rpc/$literal", "https://example.invalid/rpc/%27%5C"):
                with self.subTest(url=url):
                    config = root / ".env"
                    config.write_text(f"RPC_URL='{url}'\nCHAIN_ID=SN_SEPOLIA\n")
                    config.chmod(0o600)
                    rendered = self.render(root)["services"]["prover"]["environment"]
                    parsed = check.read_config(config, {})
                    # Compose escapes dollars when serializing reusable config.
                    self.assertEqual(rendered["RPC_URL"].replace("$$", "$"), parsed["RPC_URL"])
                    self.assertEqual(rendered["CHAIN_ID"], parsed["CHAIN_ID"])


if __name__ == "__main__":
    unittest.main()
