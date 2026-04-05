#!/usr/bin/env python3
"""
DPNN — Distributed Privacy Node Network
----------------------------------------
Un solo programma. Lo avvii, entri nella rete, scegli il paese,
navighi. Sei anche un human node — servi query agli altri.

Uso:
  python3 dpnn.py --country DE
  python3 dpnn.py --list

Nel browser dopo averlo avviato:
  http://127.0.0.1:53535/dns-query

Richiede:
  pip3 install dnslib dnspython
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import signal
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Any
from urllib.parse import urlparse, parse_qs

try:
    import dns.resolver
    import dns.exception
except ImportError:
    print("Errore: pip3 install dnspython")
    sys.exit(1)

try:
    import dnslib
    from dnslib import DNSRecord, RR, QTYPE
except ImportError:
    print("Errore: pip3 install dnslib")
    sys.exit(1)

# ================= POLICY =================
#
# DPNN Network License v1.0
# Il codice e' libero — distribuiscilo.
# Per partecipare alla rete devi essere registrato
# nella rubrica ufficiale DPNN su Decentraland/Ethereum.
#
# Indirizzo contratto ufficiale (da aggiornare al deploy):
DPNN_CONTRACT = os.getenv("DPNN_CONTRACT", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("dpnn")


def check_registration(ip: str) -> bool:
    """
    Verifica se il nodo e' registrato nella rubrica DPNN.
    Quando lo smart contract sara' deployato, questa funzione
    controllera' il contratto Ethereum.
    Per ora logga un avviso se il contratto non e' configurato.
    """
    if not DPNN_CONTRACT:
        log.warning("=" * 56)
        log.warning("DPNN Network License v1.0")
        log.warning("Per partecipare alla rete registrati su:")
        log.warning(" https://decentraland.org — cerca DPNN")
        log.warning("La rubrica ufficiale e' su Ethereum.")
        log.warning("Il codice e' libero. La rete ha una sola porta.")
        log.warning("=" * 56)
        return True  # permissivo finche' il contratto non esiste

    # TODO: verifica contratto Ethereum
    # w3 = Web3(...)
    # contract = w3.eth.contract(address=DPNN_CONTRACT, abi=DPNN_ABI)
    # return contract.functions.isRegistered(ip).call()
    return True


# ================= CONFIG =================

REPO_OWNER   = os.getenv("DPNN_REPO_OWNER", "")
REPO_NAME    = os.getenv("DPNN_REPO_NAME", "dpnn-peers")
FILE_PATH    = os.getenv("DPNN_FILE_PATH", "peers.json")
BRANCH       = os.getenv("DPNN_BRANCH", "main")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

NODE_HOST        = "0.0.0.0"
NODE_PORT        = int(os.getenv("DPNN_LISTEN_PORT", "35353"))
DOH_HOST         = "127.0.0.1"
DOH_PORT         = int(os.getenv("DPNN_DOH_PORT", "53535"))
CONNECT_TIMEOUT  = int(os.getenv("DPNN_CONNECT_TIMEOUT", "5"))
HTTP_TIMEOUT     = int(os.getenv("DPNN_HTTP_TIMEOUT", "10"))
KEEPALIVE_INTERVAL  = int(os.getenv("DPNN_KEEPALIVE_INTERVAL", "120"))
DISCOVERY_INTERVAL  = int(os.getenv("DPNN_DISCOVERY_INTERVAL", "300"))
REFRESH_INTERVAL    = int(os.getenv("DPNN_REFRESH_INTERVAL", "300"))
MAX_PEER_AGE        = int(os.getenv("DPNN_MAX_PEER_AGE", "600"))
MAX_MESSAGE_SIZE    = int(os.getenv("DPNN_MAX_MESSAGE_SIZE", "65536"))
DNS_TIMEOUT         = float(os.getenv("DPNN_DNS_TIMEOUT", "3.0"))
DNS_LIFETIME        = float(os.getenv("DPNN_DNS_LIFETIME", "5.0"))

PUBLIC_IP_SERVICES = [
    "https://api.ipify.org",
    "https://ip.seeip.org",
    "https://ifconfig.me/ip",
]

GEO_API = "http://ip-api.com/json/{ip}?fields=country,countryCode,regionName,city,org,as"


def get_registry_urls() -> list[str]:
    env = os.getenv("DPNN_REGISTRY_URLS", "").strip()
    if env:
        return [u.strip() for u in env.split(",") if u.strip()]
    if REPO_OWNER:
        return [
            f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{FILE_PATH}"
        ]
    return []


def github_registry_enabled() -> bool:
    return bool(REPO_OWNER)


# ================= STATE =================

running = True
state_lock = threading.Lock()
_my_ip = ""
_my_country = ""

dns_cache: dict[str, dict[str, Any]] = {}
known_peers: list["Peer"] = []
connected_peers: dict[str, int] = {}


# ================= PEER =================

@dataclass
class Peer:
    ip: str
    port: int
    last_seen: int
    status: str = "online"
    country: str = ""
    country_code: str = ""
    region: str = ""
    city: str = ""
    org: str = ""
    asn: str = ""
    source: str = "registry"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Optional["Peer"]:
        try:
            ip = str(data["ip"]).strip()
            port = int(data["port"])
            last_seen = int(data["last_seen"])
            if not ip or not (1 <= port <= 65535):
                return None
            return Peer(
                ip=ip,
                port=port,
                last_seen=last_seen,
                status=str(data.get("status", "online")),
                country=str(data.get("country", "")),
                country_code=str(data.get("country_code", "")),
                region=str(data.get("region", "")),
                city=str(data.get("city", "")),
                org=str(data.get("org", "")),
                asn=str(data.get("asn", "")),
                source=str(data.get("source", "registry")),
            )
        except Exception:
            return None


# ================= GEO + IP =================

def get_public_ip() -> Optional[str]:
    for url in PUBLIC_IP_SERVICES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DPNN/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip:
                    return ip
        except Exception:
            continue
    return None


def get_geo(ip: str) -> dict[str, str]:
    try:
        url = GEO_API.format(ip=ip)
        req = urllib.request.Request(url, headers={"User-Agent": "DPNN/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "country": data.get("country", ""),
                "country_code": data.get("countryCode", ""),
                "region": data.get("regionName", ""),
                "city": data.get("city", ""),
                "org": data.get("org", ""),
                "asn": data.get("as", ""),
            }
    except Exception as e:
        log.warning("Geo lookup fallito: %s", e)
        return {}


# ================= REGISTRY =================

def fetch_from_url(url: str) -> list[Peer]:
    headers: dict[str, str] = {"User-Agent": "DPNN/1.0"}
    if "api.github.com" in url and GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        headers["Accept"] = "application/vnd.github+json"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and "content" in data:
                    raw = base64.b64decode(data["content"]).decode("utf-8")
                    parsed = json.loads(raw)
                else:
                    parsed = data
            except Exception:
                parsed = json.loads(raw)

            if not isinstance(parsed, list):
                return []

            peers = [p for item in parsed if (p := Peer.from_dict(item))]
            log.info("Registry %s -> %d peer", url[:60], len(peers))
            return peers
    except Exception as e:
        log.warning("Registry %s fallito: %s", url[:60], e)
        return []


def fetch_all_peers() -> list[Peer]:
    urls = get_registry_urls()
    if not urls:
        return []

    seen: dict[tuple[str, int], Peer] = {}
    with ThreadPoolExecutor(max_workers=max(len(urls), 1)) as ex:
        futures = [ex.submit(fetch_from_url, url) for url in urls]
        for future in as_completed(futures):
            try:
                peers = future.result()
            except Exception as e:
                log.warning("Errore fetch registry: %s", e)
                continue
            for peer in peers:
                k = (peer.ip, peer.port)
                if k not in seen:
                    seen[k] = peer

    log.info("Totale peer: %d", len(seen))
    return list(seen.values())


class GithubRegistry:
    def __init__(self) -> None:
        self._etag: Optional[str] = None
        self._cache: list[Peer] = []

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "User-Agent": "DPNN/1.0"}
        if GITHUB_TOKEN:
            h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        return h

    def read(self) -> tuple[list[Peer], Optional[str]]:
        if not github_registry_enabled():
            return [], None

        url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
            f"/contents/{FILE_PATH}?ref={BRANCH}"
        )
        headers = self._headers()
        if self._etag:
            headers["If-None-Match"] = self._etag

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._etag = resp.headers.get("ETag")
                raw = base64.b64decode(data.get("content", "")).decode("utf-8")
                parsed = json.loads(raw)
                peers = [p for item in parsed if (p := Peer.from_dict(item))]
                self._cache = peers
                return peers, data.get("sha")
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return list(self._cache), None
            if e.code == 404:
                return [], None
            log.warning("GitHub read HTTP %s", e.code)
            return list(self._cache), None
        except Exception as e:
            log.warning("GitHub read error: %s", e)
            return list(self._cache), None

    def write(self, peers: list[Peer], sha: Optional[str], message: str) -> bool:
        if not github_registry_enabled():
            return False

        url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
            f"/contents/{FILE_PATH}"
        )
        encoded = base64.b64encode(
            json.dumps([asdict(p) for p in peers], indent=2).encode("utf-8")
        ).decode("utf-8")

        payload: dict[str, Any] = {
            "message": message,
            "content": encoded,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha

        headers = self._headers()
        headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT",
        )
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                resp.read()
                log.info("GitHub write OK: %s", message)
                return True
        except Exception as e:
            log.error("GitHub write error: %s", e)
            return False


registry = GithubRegistry()


# ================= PEER MANAGEMENT =================

def cleanup_peers(peers: list[Peer]) -> list[Peer]:
    cutoff = int(time.time()) - MAX_PEER_AGE
    return [p for p in peers if p.last_seen >= cutoff]


def cleanup_connected_peers() -> None:
    cutoff = int(time.time()) - MAX_PEER_AGE
    with state_lock:
        stale = [ip for ip, ts in connected_peers.items() if ts < cutoff]
        for ip in stale:
            connected_peers.pop(ip, None)


def merge_peers(new_peers: list[Peer]) -> None:
    global known_peers
    with state_lock:
        existing = {(p.ip, p.port): p for p in known_peers}
        for peer in new_peers:
            k = (peer.ip, peer.port)
            old = existing.get(k)
            if old is None or peer.last_seen > old.last_seen:
                existing[k] = peer
        known_peers = cleanup_peers(list(existing.values()))


def upsert_self(peers: list[Peer], my_ip: str, geo: dict[str, str]) -> list[Peer]:
    now = int(time.time())
    filtered = [p for p in peers if p.ip != my_ip]
    filtered.append(
        Peer(
            ip=my_ip,
            port=NODE_PORT,
            last_seen=now,
            status="online",
            country=geo.get("country", ""),
            country_code=geo.get("country_code", ""),
            region=geo.get("region", ""),
            city=geo.get("city", ""),
            org=geo.get("org", ""),
            asn=geo.get("asn", ""),
            source="self",
        )
    )
    return filtered


# ================= DNS =================

def resolve_dns(domain: str, qtype: str) -> tuple[list[str], int]:
    cache_key = f"{domain}|{qtype}"
    now = time.time()

    with state_lock:
        cached = dns_cache.get(cache_key)
        if cached and cached["expires_at"] > now:
            return cached["answers"], cached["ttl"]

    resolver = dns.resolver.Resolver()
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_LIFETIME

    try:
        answers = resolver.resolve(domain, qtype)
        ttl = answers.rrset.ttl if answers.rrset else 60
        result = [str(r) for r in answers]
        with state_lock:
            dns_cache[cache_key] = {
                "answers": result,
                "ttl": ttl,
                "expires_at": now + ttl,
            }
        return result, ttl
    except dns.resolver.NXDOMAIN:
        return [], 0
    except dns.resolver.NoAnswer:
        return [], 60
    except Exception as e:
        log.warning("DNS error %s [%s]: %s", domain, qtype, e)
        return [], 0


def resolve_via_peer(peer: Peer, qname: str, qtype: str) -> Optional[tuple[list[str], int]]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        sock.connect((peer.ip, peer.port))
        msg = json.dumps({
            "type": "DNS_QUERY",
            "domain": qname,
            "qtype": qtype,
            "timestamp": int(time.time()),
        }) + "\n"
        sock.sendall(msg.encode("utf-8"))

        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk

        line = buf.split(b"\n")[0].decode("utf-8").strip()
        if not line:
            return None

        resp = json.loads(line)
        if not resp.get("ok"):
            return None

        return resp.get("answers", []), int(resp.get("ttl", 60))
    except Exception as e:
        log.warning("Peer %s error: %s", peer.ip, e)
        return None
    finally:
        try:
            sock.close()
        except Exception:
            pass


def resolve_query(qname: str, qtype: str) -> tuple[list[str], int]:
    with state_lock:
        country = _my_country
        peers = [p for p in known_peers if p.country_code == country and p.ip != _my_ip]

    if not peers:
        log.error("Nessun peer per paese: %s", country)
        return [], 0

    for peer in peers:
        result = resolve_via_peer(peer, qname, qtype)
        if result is not None:
            log.info("Risolto %s [%s] via %s (%s)", qname, qtype, peer.ip, peer.country_code)
            return result

    log.error("Tutti i peer di %s hanno fallito per %s", country, qname)
    return [], 0


# ================= NODE SERVER =================

def send_line(sock: socket.socket, data: dict[str, Any]) -> None:
    sock.sendall((json.dumps(data) + "\n").encode("utf-8"))


def recv_line(sock: socket.socket) -> Optional[dict[str, Any]]:
    buf = b""
    while b"\n" not in buf:
        if len(buf) > MAX_MESSAGE_SIZE:
            return None
        try:
            chunk = sock.recv(4096)
            if not chunk:
                return None
            buf += chunk
        except Exception:
            return None

    try:
        line = buf.split(b"\n")[0].decode("utf-8").strip()
        return json.loads(line) if line else None
    except Exception:
        return None


def handle_peer(conn: socket.socket, addr: tuple[str, int]) -> None:
    conn.settimeout(CONNECT_TIMEOUT)
    try:
        msg = recv_line(conn)
        if not msg:
            return

        mtype = msg.get("type", "")
        if mtype == "HELLO":
            incoming = [p for item in msg.get("peers", []) if (p := Peer.from_dict(item))]
            merge_peers(incoming)
            with state_lock:
                wire = [asdict(p) for p in known_peers]
                connected_peers[addr[0]] = int(time.time())
            send_line(conn, {"type": "PEER_LIST", "ok": True, "peers": wire})
            log.info("HELLO da %s — %d peer", addr[0], len(incoming))

        elif mtype == "DNS_QUERY":
            domain = str(msg.get("domain", "")).strip()
            qtype = str(msg.get("qtype", "A")).upper()

            if not domain:
                send_line(conn, {
                    "type": "DNS_RESPONSE",
                    "ok": False,
                    "error": "MISSING_DOMAIN",
                })
                return

            answers, ttl = resolve_dns(domain, qtype)
            send_line(conn, {
                "type": "DNS_RESPONSE",
                "ok": True,
                "domain": domain,
                "qtype": qtype,
                "answers": answers,
                "ttl": ttl,
                "resolver_ip": _my_ip,
            })

        else:
            send_line(conn, {"type": "ERROR", "error": "UNKNOWN_TYPE"})
    except Exception as e:
        log.warning("Errore peer %s: %s", addr[0], e)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def start_node_server() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((NODE_HOST, NODE_PORT))
    server.listen(32)
    server.settimeout(1.0)
    log.info("Human node in ascolto su %s:%d", NODE_HOST, NODE_PORT)

    try:
        while running:
            try:
                conn, addr = server.accept()
                threading.Thread(target=handle_peer, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if running:
                    log.warning("Node server error: %s", e)
    finally:
        try:
            server.close()
        except Exception:
            pass


# ================= DOH SERVER =================

class DoHHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/status":
            self._send(200, self._status().encode("utf-8"), "text/plain; charset=utf-8")
            return

        if not self.path.startswith("/dns-query"):
            self._send(404, b"Not found", "text/plain")
            return

        params = parse_qs(urlparse(self.path).query)
        name = params.get("name", [""])[0].strip().rstrip(".")
        qtype = params.get("type", ["A"])[0].strip().upper()

        if not name:
            self._send(400, b"Missing name", "text/plain")
            return

        answers, ttl = resolve_query(name, qtype)
        self._send(
            200,
            self._json_resp(name, qtype, answers, ttl).encode("utf-8"),
            "application/dns-json",
        )

    def do_POST(self) -> None:
        if not self.path.startswith("/dns-query"):
            self._send(404, b"Not found", "text/plain")
            return

        if "dns-message" not in self.headers.get("Content-Type", ""):
            self._send(415, b"Unsupported Media Type", "text/plain")
            return

        raw_req = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            request = DNSRecord.parse(raw_req)
            qname = str(request.q.qname).rstrip(".")
            qtype = QTYPE[request.q.qtype]
        except Exception:
            self._send(400, b"Bad DNS request", "text/plain")
            return

        answers, ttl = resolve_query(qname, qtype)
        reply = request.reply()

        if answers:
            for a in answers:
                try:
                    for rr in RR.fromZone(f"{qname}. {ttl} IN {qtype} {a}"):
                        reply.add_answer(rr)
                except Exception:
                    pass
        else:
            reply.header.rcode = dnslib.RCODE.SERVFAIL

        self._send(200, reply.pack(), "application/dns-message")

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _json_resp(self, name: str, qtype: str, answers: list[str], ttl: int) -> str:
        qt = {
            "A": 1,
            "AAAA": 28,
            "MX": 15,
            "TXT": 16,
            "CNAME": 5,
            "NS": 2,
        }.get(qtype, 1)

        return json.dumps({
            "Status": 0 if answers else 2,
            "TC": False,
            "RD": True,
            "RA": True,
            "AD": False,
            "CD": False,
            "Question": [{"name": name, "type": qt}],
            "Answer": [
                {"name": name, "type": qt, "TTL": ttl, "data": a}
                for a in answers
            ],
        })

    def _status(self) -> str:
        cleanup_connected_peers()
        with state_lock:
            peers = len(known_peers)
            connected = len(connected_peers)
            cache = len(dns_cache)

        return (
            f"DPNN v1.0\n"
            f"IP:        {_my_ip}:{NODE_PORT}\n"
            f"Country:   {_my_country}\n"
            f"Peers:     {peers} known, {connected} connected\n"
            f"DNS cache: {cache} entries\n"
            f"DoH:       http://{DOH_HOST}:{DOH_PORT}/dns-query\n"
        )


class ThreadedHTTPServer(HTTPServer):
    def process_request(self, request: Any, client_address: Any) -> None:
        threading.Thread(
            target=self._handle,
            args=(request, client_address),
            daemon=True,
        ).start()

    def _handle(self, request: Any, client_address: Any) -> None:
        try:
            self.finish_request(request, client_address)
        except Exception:
            pass
        finally:
            self.shutdown_request(request)


# ================= BACKGROUND LOOPS =================

def keepalive_loop(my_ip: str, geo: dict[str, str]) -> None:
    while running:
        time.sleep(KEEPALIVE_INTERVAL)
        if not running:
            break

        peers, sha = registry.read()
        peers = cleanup_peers(peers)
        peers = upsert_self(peers, my_ip, geo)
        merge_peers(peers)
        registry.write(peers, sha, f"keepalive {my_ip}")
        log.info("Keepalive — %d peer nel registry", len(peers))


def discovery_loop() -> None:
    while running:
        time.sleep(DISCOVERY_INTERVAL)
        if not running:
            break

        cleanup_connected_peers()

        with state_lock:
            targets = [
                p for p in known_peers
                if p.ip not in connected_peers and p.ip != _my_ip
            ]

        for peer in targets[:5]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(CONNECT_TIMEOUT)
                sock.connect((peer.ip, peer.port))

                with state_lock:
                    wire = [asdict(p) for p in known_peers]

                send_line(sock, {
                    "type": "HELLO",
                    "peers": wire,
                    "timestamp": int(time.time()),
                })

                resp = recv_line(sock)
                sock.close()

                if resp and resp.get("type") == "PEER_LIST":
                    incoming = [p for item in resp.get("peers", []) if (p := Peer.from_dict(item))]
                    merge_peers(incoming)
                    with state_lock:
                        connected_peers[peer.ip] = int(time.time())
                    log.info("Discovery: connesso a %s", peer.ip)
            except Exception:
                pass


def registry_refresh_loop() -> None:
    while running:
        time.sleep(REFRESH_INTERVAL)
        if not running:
            break

        peers = fetch_all_peers()
        if peers:
            merge_peers(peers)


# ================= SIGNAL =================

def signal_handler(sig: int, frame: Any) -> None:
    global running
    log.info("Arresto DPNN...")
    running = False


# ================= COMMANDS =================

def cmd_list() -> int:
    log.info("Scarico peer dal registry...")
    peers = fetch_all_peers()
    if not peers:
        print("Nessun peer trovato.")
        return 0

    countries: dict[str, int] = {}
    for p in peers:
        c = p.country_code or "??"
        countries[c] = countries.get(c, 0) + 1

    print("\nPaesi disponibili:\n")
    for c in sorted(countries):
        n = countries[c]
        print(f"  {c}  ({n} human node{'s' if n > 1 else ''})")
    print(f"\n  Totale: {len(peers)} human nodes\n")
    return 0


def cmd_run(country: str) -> int:
    global running, _my_ip, _my_country

    if not get_registry_urls():
        log.error("Imposta DPNN_REGISTRY_URLS per il bootstrap dei peer")
        return 1

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    log.info("Rilevo IP pubblico...")
    my_ip = get_public_ip()
    if not my_ip:
        log.error("Impossibile rilevare IP pubblico")
        return 1

    _my_ip = my_ip
    log.info("IP: %s", my_ip)

    if not check_registration(my_ip):
        log.error("Nodo non registrato nella rubrica DPNN.")
        log.error("Registrati su Decentraland per partecipare.")
        return 1

    log.info("Rilevo posizione geografica...")
    geo = get_geo(my_ip)
    if geo:
        log.info("Posizione: %s, %s — %s", geo.get("city"), geo.get("country"), geo.get("org"))
    else:
        log.warning("Geo non disponibile")

    log.info("Scarico peer dal registry...")
    peers = fetch_all_peers()
    merge_peers(peers)

    _my_country = country.upper()

    with state_lock:
        available = [p for p in known_peers if p.country_code == _my_country and p.ip != my_ip]

    if not available:
        with state_lock:
            all_c = sorted(set(p.country_code for p in known_peers if p.country_code))
        log.error("Nessun peer per paese: %s", _my_country)
        if all_c:
            log.error("Paesi disponibili: %s", ", ".join(all_c))
        return 1

    log.info("Paese: %s — %d human node disponibili", _my_country, len(available))

    if GITHUB_TOKEN and github_registry_enabled():
        peers_reg, sha = registry.read()
        peers_reg = cleanup_peers(peers_reg)
        peers_reg = upsert_self(peers_reg, my_ip, geo)
        merge_peers(peers_reg)
        ok = registry.write(peers_reg, sha, f"join {my_ip}:{NODE_PORT}")
        if ok:
            log.info("Registrato come human node")
        else:
            log.warning("Registrazione fallita — solo client")
    else:
        log.info("Nessun GITHUB_TOKEN o GitHub registry non configurato — solo client")

    threads = [
        threading.Thread(target=start_node_server, daemon=True),
        threading.Thread(target=registry_refresh_loop, daemon=True),
        threading.Thread(target=discovery_loop, daemon=True),
    ]

    if GITHUB_TOKEN and github_registry_enabled():
        threads.append(
            threading.Thread(target=keepalive_loop, args=(my_ip, geo), daemon=True)
        )

    for t in threads:
        t.start()

    doh_server = ThreadedHTTPServer((DOH_HOST, DOH_PORT), DoHHandler)
    threading.Thread(target=doh_server.serve_forever, daemon=True).start()

    log.info("=" * 58)
    log.info("DPNN v1.0 attivo")
    log.info("Sei un human node — stai contribuendo la tua rete.")
    log.info("Paese scelto: %s", _my_country)
    log.info("Browser DNS: http://127.0.0.1:%d/dns-query", DOH_PORT)
    log.info("Stato: http://127.0.0.1:%d/status", DOH_PORT)
    log.info("=" * 58)
    log.info("CTRL+C per fermare.")

    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
    finally:
        try:
            doh_server.shutdown()
        except Exception:
            pass
        try:
            doh_server.server_close()
        except Exception:
            pass

    log.info("DPNN fermato.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DPNN — Distributed Privacy Node Network"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--country", "-c", metavar="XX",
        help="Paese scelto (es: DE, FR, CH, US)")
    group.add_argument("--list", "-l", action="store_true",
        help="Mostra i paesi disponibili")

    args = parser.parse_args()

    if args.list:
        return cmd_list()
    return cmd_run(args.country)


if __name__ == "__main__":
    sys.exit(main())
