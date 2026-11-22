"""
End-to-end test over stdio against a real supervisord with Basic auth.

Checks the 1.1.0 guarantees on the wire:
  * every line the server writes to stdout is JSON-RPC (logs go to stderr)
  * the Basic auth password never appears in stdout or stderr
  * get_logs responses stay bounded even for multi-megabyte logs
  * tool failures are reported with isError=true

Skipped when the ``supervisord`` executable is not available.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import xmlrpc.client
from pathlib import Path

import pytest

from supervisord_mcp.manager import MAX_LOG_BYTES

pytestmark = pytest.mark.integration

SUPERVISORD = shutil.which("supervisord")
USER = "audituser"
PASSWORD = "S3cretPW-integration"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def supervisord(tmp_path: Path):
    if SUPERVISORD is None:
        pytest.skip("supervisord executable not found")
    port = _free_port()
    # ~4 MB of log output, including a secret-looking line at the start.
    script = tmp_path / "noisy.py"
    script.write_text(
        "import sys, time\n"
        "print('SECRET_TOKEN=tok-abc123')\n"
        "for i in range(60000):\n"
        "    print('line-' + str(i).zfill(7) + ' ' + 'x' * 60)\n"
        "sys.stdout.flush()\n"
        "time.sleep(3600)\n"
    )
    noisy = f"{sys.executable} -u {script}"
    conf = tmp_path / "supervisord.conf"
    conf.write_text(
        f"""
[supervisord]
nodaemon=true
logfile={tmp_path}/supervisord.log
pidfile={tmp_path}/supervisord.pid
childlogdir={tmp_path}

[inet_http_server]
port=127.0.0.1:{port}
username={USER}
password={PASSWORD}

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[program:noisy]
command={noisy}
autostart=true
autorestart=false
stdout_logfile={tmp_path}/noisy.out.log
stdout_logfile_maxbytes=50MB
"""
    )
    proc = subprocess.Popen(
        [SUPERVISORD, "-c", str(conf)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    url = f"http://127.0.0.1:{port}/RPC2"
    proxy = xmlrpc.client.ServerProxy(f"http://{USER}:{PASSWORD}@127.0.0.1:{port}/RPC2")
    deadline = time.time() + 30
    while True:
        try:
            info = proxy.supervisor.getProcessInfo("noisy")
            log_size = os.path.getsize(tmp_path / "noisy.out.log")
            if info["statename"] == "RUNNING" and log_size > 3_000_000:
                break
        except Exception:
            pass
        if time.time() > deadline:
            proc.terminate()
            pytest.fail("supervisord did not become ready")
        time.sleep(0.2)
    yield url
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


class StdioClient:
    def __init__(self, args: list[str], env: dict[str, str]):
        self.proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )
        self.stdout_lines: list[str] = []
        self._id = 0

    def send(self, method: str, params: dict | None = None, notify: bool = False) -> dict | None:
        msg: dict = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self._id += 1
            msg["id"] = self._id
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        if notify:
            return None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise AssertionError("server closed stdout")
            self.stdout_lines.append(line)
            # Every stdout line must be JSON-RPC.
            data = json.loads(line)
            assert data.get("jsonrpc") == "2.0", line[:200]
            if data.get("id") == self._id:
                return data

    def close(self) -> str:
        assert self.proc.stdin is not None and self.proc.stderr is not None
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        return self.proc.stderr.read()


def _run_client(url_arg: list[str], extra_env: dict[str, str]) -> tuple[StdioClient, dict]:
    env = {**os.environ, **extra_env}
    client = StdioClient([sys.executable, "-m", "supervisord_mcp.main", *url_arg, "mcp"], env=env)
    client.send(
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0"},
        },
    )
    client.send("notifications/initialized", notify=True)
    tools = client.send("tools/list")
    assert tools is not None
    return client, tools


def _text(resp: dict | None) -> str:
    assert resp is not None and "result" in resp, resp
    return "".join(c.get("text", "") for c in resp["result"]["content"])


@pytest.mark.parametrize("mode", ["url", "env"])
def test_stdio_clean_bounded_and_no_secret(supervisord: str, mode: str):
    if mode == "url":
        host = supervisord.removeprefix("http://")
        url_arg = ["--server-url", f"http://{USER}:{PASSWORD}@{host}"]
        env: dict[str, str] = {}
    else:
        url_arg = []
        env = {
            "SUPERVISORD_URL": supervisord,
            "SUPERVISORD_USERNAME": USER,
            "SUPERVISORD_PASSWORD": PASSWORD,
        }
    client, tools = _run_client(url_arg, env)
    names = {t["name"] for t in tools["result"]["tools"]}
    assert {"get_logs", "get_system_info", "list_processes"} <= names

    info = client.send("tools/call", {"name": "get_system_info", "arguments": {}})
    info_text = _text(info)
    assert info["result"]["isError"] is False
    assert "Server URL: " + supervisord in info_text
    assert PASSWORD not in info_text

    listing = client.send("tools/call", {"name": "list_processes", "arguments": {}})
    assert "noisy: RUNNING" in _text(listing)

    default_logs = client.send("tools/call", {"name": "get_logs", "arguments": {"name": "noisy"}})
    default_text = _text(default_logs)
    assert default_logs["result"]["isError"] is False
    assert "older output omitted" in default_text
    assert default_text.count("line-") == 100

    big = client.send(
        "tools/call",
        {
            "name": "get_logs",
            "arguments": {"name": "noisy", "lines": 1000, "max_bytes": MAX_LOG_BYTES},
        },
    )
    big_text = _text(big)
    assert len(big_text) <= MAX_LOG_BYTES + 200
    assert "SECRET_TOKEN" not in big_text  # beginning of the log is out of the window

    huge = client.send(
        "tools/call", {"name": "get_logs", "arguments": {"name": "noisy", "lines": 5_000_000}}
    )
    assert huge["result"]["isError"] is True
    negative = client.send(
        "tools/call", {"name": "get_logs", "arguments": {"name": "noisy", "lines": -10}}
    )
    assert negative["result"]["isError"] is True
    assert len(_text(negative)) < 1000

    missing = client.send("tools/call", {"name": "start_process", "arguments": {"name": "nope"}})
    assert missing["result"]["isError"] is True
    assert "BAD_NAME" in _text(missing)

    stderr = client.close()
    stdout = "".join(client.stdout_lines)
    assert PASSWORD not in stdout
    assert PASSWORD not in stderr
