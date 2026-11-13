"""Gemeinsame Unit-Test-Isolierung: kein echtes Netz."""

from __future__ import annotations

import socket

import pytest

ALLOWED = {"localhost", "127.0.0.1", "::1", "localhost.localdomain", "ip6-localhost"}


def _loopback(host: object) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    value = str(host).strip("[]").lower()
    return value in ALLOWED or value.startswith("127.")


@pytest.fixture(autouse=True)
def _block_real_network(monkeypatch):
    real_getaddrinfo = socket.getaddrinfo
    real_connect = socket.socket.connect

    def guarded_getaddrinfo(host, *args, **kwargs):
        if not _loopback(host):
            raise socket.gaierror(socket.EAI_NONAME, f"unit test network blocked: {host!r}")
        return real_getaddrinfo(host, *args, **kwargs)

    def guarded_connect(self, address):
        if isinstance(address, tuple) and not _loopback(address[0]):
            raise ConnectionRefusedError(f"unit test network blocked: {address[0]}")
        return real_connect(self, address)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
