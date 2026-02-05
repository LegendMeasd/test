import socket
from unittest import mock

import pytest

from subdomain_finder.src import subdomain_finder


def test_load_wordlist(tmp_path):
    p = tmp_path / "wl.txt"
    p.write_text("a\nb\n#comment\nc\n")
    labels = subdomain_finder.load_wordlist(p)
    assert labels == ["a", "b", "c"]


def test_resolve_host_success_and_failure():
    # Patch socket.gethostbyname to control behavior
    def side_effect(host):
        if host.startswith("exists."):
            return "1.2.3.4"
        raise socket.gaierror()
    
    with mock.patch("subdomain_finder.src.subdomain_finder.socket.gethostbyname", side_effect=side_effect):
        assert subdomain_finder.resolve_host("exists.example.com") == "1.2.3.4"
        assert subdomain_finder.resolve_host("nope.example.com") is None


def test_find_subdomains_with_mocked_dns(monkeypatch):
    labels = ["exists", "nope"]

    def fake_gethostbyname(host):
        if host.startswith("exists."):
            return "5.6.7.8"
        raise socket.gaierror()

    monkeypatch.setattr(socket, "gethostbyname", fake_gethostbyname)

    results = list(subdomain_finder.find_subdomains("example.com", labels, threads=2, http_probe=False))
    assert len(results) == 1
    assert results[0]["subdomain"] == "exists.example.com"
    assert results[0]["ip"] == "5.6.7.8"
