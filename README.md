# DPNN — Distributed Privacy Node Network

DNS answers are no longer universal.

They depend on who is asking — and from where.

DPNN lets you observe the internet as it appears from real networks around the world.

---

## What DPNN is

DPNN is a distributed network of real users sharing DNS resolution perspectives.

When you run DPNN:

* you query DNS from other countries
* you use real user networks (not datacenter resolvers)
* you also contribute your own network to others

There is no separation between client and node.

**Every user is a human node.**

---

## The problem

DNS is not globally consistent.

The same domain may resolve differently depending on:

* country
* ISP
* network policies
* CDN geolocation
* filtering or blocking rules

Traditional tools (public DNS, VPNs) do not show the real behavior of DNS across actual user networks.

DPNN is built to observe that reality.

---

## What DPNN does

DPNN lets you send DNS queries through a real user in another network.

That user's machine resolves the domain using its own system DNS.

You receive the answer that network sees.

This is not:

* a public DNS resolver
* a VPN
* a proxy
* a centralized service

It is a **network of human nodes**.

---

## How it works
your browser
↓  DNS query (DoH)
DPNN (local) 127.0.0.1:53535
↓  DPNN protocol (TCP/JSON)
human node (real user, chosen country)
↓  system DNS
authoritative nameserver
↑
human node
↑
DPNN local
↑
your browser

---

## Architecture

DPNN is a **single program**.

When you start it, it:

* joins the DPNN network
* exposes a local DNS-over-HTTPS endpoint
* communicates with other nodes
* serves DNS queries to other users

There is no central server.

The network is made of participants.

---

## Human node

A human node is any real user running DPNN on a real network:

* home connection
* mobile network
* office network

The value of DPNN comes from these real network conditions.

Not from servers.

---

## Use cases

* Compare DNS across countries and ISPs
* Detect filtering or censorship
* Observe CDN geolocation behavior
* Analyze split-horizon DNS
* Debug region-specific DNS issues

---

## Installation
```bash
git clone https://github.com/nardaxxx/dpnn.git
cd dpnn
pip3 install dnslib dnspython
```

Requirements:

* Python 3.9 or newer
* No root privileges required

---

## Bootstrap configuration

DPNN uses a temporary bootstrap registry for peer discovery.

Set your registry directly:
```bash
export DPNN_REGISTRY_URLS="https://raw.githubusercontent.com/nardaxxx/dpnn-peers/main/peers.json"
```

Or set the GitHub repo variables:
```bash
export DPNN_REPO_OWNER="nardaxxx"
export DPNN_REPO_NAME="dpnn-peers"
```

To register as a writable human node, also set:
```bash
export GITHUB_TOKEN="your_token_here"
```

Without a token, DPNN runs in read-only client mode.

---

## List available countries
```bash
python3 dpnn.py --list
```

---

## Start DPNN
```bash
python3 dpnn.py --country DE
```

---

## Configure your browser

Set DNS over HTTPS (DoH) to:
http://127.0.0.1:53535/dns-query

---

## Check status
```bash
curl http://127.0.0.1:53535/status
```

---

## Test manually
```bash
curl "http://127.0.0.1:53535/dns-query?name=example.com&type=A"
```

---

## Current limitations (v1 prototype)

* on-chain registration is not yet active — the network is open for testing
* DNS responses are not verified across multiple peers
* node identity is not signed
* traffic between nodes is not encrypted

These are known limitations of v1. See the roadmap.

---

## Network model

DPNN currently uses a bootstrap registry for peer discovery.

This registry:

* is temporary
* is not authoritative
* is not part of the final network model

Peers discovered through it are not verified.

---

## Future model

DPNN is designed to evolve into:

* on-chain node registry (Ethereum)
* signed node identities
* fee-based participation
* decentralized peer discovery

The bootstrap registry will be removed.

---

## Security and trust model

DPNN is an observation network.

It does NOT guarantee:

* correctness of responses
* anonymity of users
* censorship resistance
* verified node identity

A node may:

* return incorrect data
* operate on a filtered network
* misrepresent its location

Human nodes can see your DNS queries.

---

## DoH support

* DNS over HTTPS (RFC 8484-style)
* supports GET and POST
* reconstructs DNS answers from remote nodes
* does not fall back silently to external DNS

---

## Status

DPNN v1 is a functional experimental prototype.

* peer discovery works
* DNS queries across networks work
* local DoH endpoint works

The network is experimental and evolving.

---

## Roadmap

### Stage 1 — Current

* [x] working protocol
* [x] peer discovery
* [x] human node participation
* [x] local DoH resolver

### Stage 2

* [ ] local peer cache
* [ ] multi-peer verification mode
* [ ] node reliability scoring
* [ ] improved DNS error handling

### Stage 3

* [ ] signed node identities
* [ ] decentralized registry
* [ ] removal of bootstrap dependency

### Stage 4

* [ ] on-chain registry
* [ ] fee-based participation
* [ ] fully self-sustaining network

---

## Philosophy

DPNN does not try to fix DNS.

It shows what DNS actually is.

---

## Contributing

* run DPNN on your network
* test from different countries and ISPs
* report issues
* improve the protocol

Every new node increases the value of the network.

---

## Final note

DPNN is built for observation, research, and resilience.

In a fragmented or degraded internet, understanding how networks actually behave becomes critical.

DPNN is designed for that.
