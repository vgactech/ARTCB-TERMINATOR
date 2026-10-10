"""ARTCB MCP Bridge — HTTP-only adapter for ARTCB-TERMINATOR.

Connects to the ARTCB MCP server via JSON-RPC over HTTP.
NEVER imports from the artcb source tree. The artcb repository
is a black box reachable only through its network interface.

Usage:
    bridge = ArtcbMcpBridge()
    if bridge.is_available():
        result = bridge.call_tool("artcb_chain_verify", {})
        result = bridge.call_tool("artcb_memory_event", {
            "event_id": "evt-123",
            "content": "Guardian blocked wallet.sign",
            "kind": "security_event",
            "visibility": "private",
        })

Environment (from Doppler artcb-blockchain/dev):
    ARTCB_API_URL    — base URL of the ARTCB API (default http://localhost:8000)
    ARTCB_API_KEY    — operator key (Bearer token)
    ARTCB_AGENT_ID   — agent identity header
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
import uuid
from typing import Any

logger = logging.getLogger("artcb.bridge")

_MCP_VERSION = "2024-11-05"
_SERVER_NAME = "artcb-blockchain"


class ArtcbMcpBridge:
    """HTTP-only bridge to the ARTCB MCP server.

    Sends JSON-RPC 2.0 requests to ARTCB_API_URL/mcp (HTTP endpoint)
    or falls back to direct API calls.

    This class never imports artcb source code. It is safe to use
    in ARTCB-TERMINATOR without coupling to the artcb repository.
    """

    def __init__(self) -> None:
        self._api_url = (
            os.environ.get("ARTCB_API_URL", "").rstrip("/")
            or "http://localhost:8000"
        )
        self._api_key = os.environ.get("ARTCB_API_KEY", "")
        self._agent_id = os.environ.get("ARTCB_AGENT_ID", "terminator-guardian")
        self._timeout = 10
        self._initialized = False
        self._server_info: dict[str, Any] = {}
        self._available_tools: list[str] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the ARTCB API is reachable and the MCP server responds."""
        try:
            self._ensure_initialized()
            return bool(self._server_info)
        except Exception as exc:
            logger.debug("ARTCB bridge unavailable: %s", exc)
            return False

    def health(self) -> dict[str, Any]:
        """Return availability status without raising."""
        try:
            self._ensure_initialized()
            return {
                "available": True,
                "api_url": self._api_url,
                "server_name": self._server_info.get("name", _SERVER_NAME),
                "server_version": self._server_info.get("version", "?"),
                "tools": self._available_tools,
                "tool_count": len(self._available_tools),
            }
        except Exception as exc:
            return {
                "available": False,
                "api_url": self._api_url,
                "error": str(exc)[:120],
                "tools": [],
                "tool_count": 0,
            }

    def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Call an ARTCB MCP tool and return the result.

        Raises RuntimeError if the bridge is unavailable or the call fails.
        Correlation IDs are attached for forensic traceability.
        """
        self._ensure_initialized()
        correlation_id = f"terminator:{uuid.uuid4()}"
        request_payload = {
            "jsonrpc": "2.0",
            "id": correlation_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        logger.info(
            "ARTCB MCP call tool=%s correlation=%s", tool_name, correlation_id
        )
        response = self._post_mcp(request_payload)
        if "error" in response:
            raise RuntimeError(
                f"ARTCB MCP error {response['error'].get('code')}: "
                f"{response['error'].get('message', 'unknown')}"
            )
        result = response.get("result", {})
        return {
            "tool": tool_name,
            "correlation_id": correlation_id,
            "api_url": self._api_url,
            "content": result.get("content", []),
            "is_error": result.get("isError", False),
        }

    def chain_verify(self) -> dict[str, Any]:
        """Shortcut: verify ARTCB chain integrity."""
        return self.call_tool("artcb_chain_verify", {})

    def record_guardian_event(
        self,
        event_id: str,
        content: str,
        kind: str = "security_event",
    ) -> dict[str, Any]:
        """Shortcut: record a Guardian security event into ARTCB memory."""
        return self.call_tool(
            "artcb_memory_event",
            {
                "event_id": event_id,
                "content": content,
                "kind": kind,
                "visibility": "private",
            },
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        # Send MCP initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {"protocolVersion": _MCP_VERSION},
        }
        resp = self._post_mcp(init_payload)
        if "error" in resp:
            raise RuntimeError(f"MCP initialize failed: {resp['error']}")
        result = resp.get("result", {})
        self._server_info = result.get("serverInfo", {})
        # Fetch tool list
        tools_resp = self._post_mcp(
            {"jsonrpc": "2.0", "id": "tools-1", "method": "tools/list", "params": {}}
        )
        self._available_tools = [
            t["name"]
            for t in tools_resp.get("result", {}).get("tools", [])
        ]
        self._initialized = True
        logger.info(
            "ARTCB bridge initialized: server=%s tools=%d",
            self._server_info.get("name"),
            len(self._available_tools),
        )

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        if self._agent_id:
            h["X-ARTCB-Agent-Id"] = self._agent_id
        return h

    def _post_mcp(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a JSON-RPC payload to the ARTCB MCP HTTP endpoint."""
        # Try /mcp HTTP endpoint first (ARTCB server.py HTTP mode)
        url = f"{self._api_url}/mcp"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:200]
            raise RuntimeError(f"ARTCB MCP HTTP {exc.code}: {detail}") from exc
        except OSError as exc:
            raise RuntimeError(f"ARTCB API unreachable at {url}: {exc}") from exc
