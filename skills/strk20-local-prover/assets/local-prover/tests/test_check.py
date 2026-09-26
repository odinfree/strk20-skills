import contextlib
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

spec = importlib.util.spec_from_file_location("prover_check", Path(__file__).parents[1] / "check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


@contextlib.contextmanager
def server(reply):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            status, headers, data = reply(body)
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", requests
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


def replies(chain="SN_SEPOLIA", version="0.10.3-rc.2"):
    values = {"starknet_specVersion": version,
              "starknet_chainId": check.CHAIN_IDS[chain], "starknet_blockNumber": 123}
    return lambda body: (200, {}, {"jsonrpc": "2.0", "id": body["id"], "result": values[body["method"]]})


class ConfigTests(unittest.TestCase):
    def test_literal_secret_preserved_without_evaluation_and_shell_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("RPC_URL='https://example.invalid/a$literal'\nCHAIN_ID=SN_SEPOLIA\n")
            path.chmod(0o600)
            config = check.read_config(path, {"CHAIN_ID": "SN_MAIN"})
            self.assertEqual(config["RPC_URL"], "https://example.invalid/a$literal")
            self.assertEqual(config["CHAIN_ID"], "SN_MAIN")

    def test_rejects_world_readable_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("RPC_URL='https://example.invalid/private'\n")
            path.chmod(0o644)
            with self.assertRaisesRegex(check.CheckError, "chmod 600"):
                check.read_config(path, {})

    def test_rejects_expression_without_echoing_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("RPC_URL=${DO_NOT_PRINT_ME}\n")
            path.chmod(0o600)
            with self.assertRaises(check.CheckError) as caught:
                check.read_config(path, {})
            self.assertNotIn("DO_NOT_PRINT_ME", str(caught.exception))

    def test_rejects_invalid_encoding_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_bytes(b"RPC_URL=\xff\n")
            path.chmod(0o600)
            with self.assertRaises(check.CheckError):
                check.read_config(path, {})

    def test_rejects_quote_escapes_that_compose_would_interpret_differently(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("RPC_URL='https://example.invalid/SYNTHETIC_CREDENTIAL\\'suffix'\n")
            path.chmod(0o600)
            with self.assertRaises(check.CheckError) as caught:
                check.read_config(path, {})
            self.assertNotIn("SYNTHETIC_CREDENTIAL", str(caught.exception))


class DockerTests(unittest.TestCase):
    def inspect(self, **values):
        data = {"Os": "linux", "Arch": "amd64", "Version": "29.8.1", **values}
        with mock.patch.object(check.subprocess, "run") as run:
            run.return_value.stdout = json.dumps(data)
            return check.check_docker()

    def test_compatible_server_accepted(self):
        self.assertEqual(self.inspect()["platform"], "linux/amd64")
        self.assertEqual(self.inspect(Version="28.0.0")["version"], "28.0.0")

    def test_older_and_unrecognized_versions_rejected(self):
        for value in ("27.5.1", "28.0.0-rc.1", "unknown", None, 28):
            with self.subTest(version=value), self.assertRaises(check.CheckError):
                self.inspect(Version=value)

    def test_unsupported_server_platform_rejected(self):
        for values in ({"Os": "windows"}, {"Arch": "arm64"}):
            with self.subTest(values=values), self.assertRaises(check.CheckError):
                self.inspect(**values)

    def test_daemon_failure_does_not_disclose_context(self):
        errors = (check.subprocess.CalledProcessError(1, "docker", stderr="SYNTHETIC_CREDENTIAL"),
                  check.subprocess.TimeoutExpired("SYNTHETIC_CREDENTIAL", 20),
                  OSError("SYNTHETIC_CREDENTIAL"))
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(check.subprocess, "run", side_effect=error):
                    with self.assertRaises(check.CheckError) as caught:
                        check.check_docker()
                    self.assertNotIn("SYNTHETIC_CREDENTIAL", str(caught.exception))


class RpcTests(unittest.TestCase):
    def test_malformed_url_does_not_expose_credential_in_exception(self):
        for suffix in [' bad', '\tbad', '\nbad', '\x7fbad']:
            with self.subTest(suffix=repr(suffix)):
                with self.assertRaises(check.CheckError) as caught:
                    check.rpc('http://127.0.0.1:1/SYNTHETIC_CREDENTIAL' + suffix, 'starknet_specVersion')
                self.assertNotIn('SYNTHETIC_CREDENTIAL', str(caught.exception))

    def test_http_protocol_error_does_not_expose_response(self):
        with mock.patch.object(check.urllib.request, 'build_opener') as build:
            build.return_value.open.side_effect = http.client.BadStatusLine('SYNTHETIC_CREDENTIAL')
            with self.assertRaises(check.CheckError) as caught:
                check.rpc('https://example.invalid/rpc', 'starknet_specVersion')
            self.assertNotIn('SYNTHETIC_CREDENTIAL', str(caught.exception))

    def test_chain_and_version_verified_with_read_only_methods(self):
        with server(replies()) as (url, requests):
            result = check.check_upstream({"RPC_URL": url, "CHAIN_ID": "SN_SEPOLIA"})
            self.assertEqual(result["chain"], "SN_SEPOLIA")
            self.assertEqual(result["blockNumber"], 123)
            self.assertEqual({r["method"] for r in requests}, check.ALLOWED_METHODS)

    def test_wrong_chain_rejected(self):
        with server(replies("SN_MAIN")) as (url, _):
            with self.assertRaisesRegex(check.CheckError, "does not match"):
                check.check_upstream({"RPC_URL": url, "CHAIN_ID": "SN_SEPOLIA"})

    def test_incompatible_version_rejected(self):
        with server(replies(version="0.9.0")) as (url, _):
            with self.assertRaisesRegex(check.CheckError, "v0.10"):
                check.version(url)

    def test_rpc_error_body_not_disclosed(self):
        secret = "synthetic-secret-must-not-appear"
        def reply(body):
            return 200, {}, {"jsonrpc": "2.0", "id": 1, "error": {"message": secret}}
        with server(reply) as (url, _):
            with self.assertRaises(check.CheckError) as caught:
                check.rpc(url, "starknet_specVersion")
            self.assertNotIn(secret, str(caught.exception))

    def test_redirect_does_not_forward_request(self):
        with server(replies()) as (target, target_requests):
            def redirect(body):
                return 307, {"Location": target + "/synthetic-secret"}, {}
            with server(redirect) as (url, _):
                with self.assertRaisesRegex(check.CheckError, "HTTP 307"):
                    check.rpc(url, "starknet_specVersion")
            self.assertEqual(target_requests, [])

    def test_submission_method_never_sent(self):
        with server(replies()) as (url, requests):
            with self.assertRaises(check.CheckError):
                check.rpc(url, "starknet_addInvokeTransaction")
            self.assertEqual(requests, [])

    def test_public_plaintext_url_and_template_rejected(self):
        for url in ["http://example.invalid/private", "https://example.invalid/REPLACE_ME"]:
            with self.subTest(url=url), self.assertRaises(check.CheckError):
                check.validate_url(url)

    def test_log_urls_redacted(self):
        secret_url = "https://node.example.invalid/rpc/synthetic-secret"
        text = check.redact(f'error {secret_url} and "wss://node.example.invalid/ws/key"', {"RPC_URL": secret_url})
        self.assertNotIn("synthetic-secret", text)
        self.assertNotIn("/ws/key", text)
        self.assertIn("REDACTED", text)

    def test_log_url_redaction_is_case_insensitive(self):
        for scheme in ("HTTPS", "hTTp", "WSS", "Ws"):
            with self.subTest(scheme=scheme):
                text = check.redact(f"error {scheme}://example.invalid/SYNTHETIC_CREDENTIAL", {})
                self.assertNotIn("SYNTHETIC_CREDENTIAL", text)


if __name__ == "__main__":
    unittest.main()
