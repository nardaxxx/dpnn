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

That user’s machine resolves the domain using its own system DNS.

You receive the exact answer that network sees.

This is not:

* a public DNS resolver
* a VPN
* a proxy
* a centralized service

It is a **network of human nodes**.

---

## How it works

```
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
```

---

## Architecture

DPNN is a **single program**.

When you start it, it:

* joins the DPNN network
* exposes a local DNS-over-HTTPS endpoint
* communicates with other nodes
* can serve DNS queries to other users

There is no central server.

The network is made of participants.

---

## Human node

A human node is any real user running DPNN on a real network.

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

## Quick start

### Install

```bash
git clone https://github.com/YOUR_USER/dpnn.git
cd dpnn
pip3 install dnslib dnspython
```

Python 3.9+ — no root required.

---

### Configure bootstrap registry (temporary)

```bash
export DPNN_REGISTRY_URLS="https://example.com/peers.json"
```

This is **temporary** and used only for peer discovery.

---

### List available countries

```bash
python3 dpnn.py --list
```

---

### Start DPNN

```bash
python3 dpnn.py --country DE
```

---

### Configure your browser

Use DoH:

```
http://127.0.0.1:53535/dns-query
```

---

### Test

```bash
curl "http://127.0.0.1:53535/dns-query?name=example.com&type=A"
```

---

## Network model

DPNN currently uses a **bootstrap registry** to discover peers.

This registry:

* is temporary
* is not authoritative
* is not decentralized yet

---

## Future model

DPNN is designed to evolve into:

* on-chain node registry (Ethereum)
* signed node identities
* participation fees
* decentralized peer discovery

The current registry will be replaced.

---

## Security and trust model

DPNN is an **observation network**, not a trustless system.

It does NOT guarantee:

* correctness of DNS responses
* anonymity of queries
* resistance to censorship
* verified identity of nodes

A node may:

* return incorrect data
* be filtered or manipulated
* misrepresent its location

Human nodes can see your queries.

---

## DoH support

* supports DNS over HTTPS (RFC 8484 style)
* supports GET and POST
* reconstructs DNS responses from remote nodes
* no silent fallback to external resolvers

---

## Status

DPNN v1 is functional.

* peer discovery works
* DNS queries across networks work
* local DoH endpoint works

The network model is experimental and evolving.

---

## Roadmap

### Stage 1 — Current

* [x] working network protocol
* [x] peer discovery
* [x] human node model
* [x] local DoH

### Stage 2

* [ ] local peer cache
* [ ] multi-peer verification mode
* [ ] node scoring / reliability
* [ ] better DNS error handling

### Stage 3

* [ ] signed identities
* [ ] decentralized registry
* [ ] no bootstrap dependency

### Stage 4

* [ ] on-chain registry
* [ ] fee-based participation
* [ ] self-sustaining network

---

## Philosophy

DPNN does not try to fix DNS.

It shows what DNS actually is.

---

## Contributing

* run a node
* open issues
* improve protocol
* test from different networks

Every new node adds value.

---

## Final note

DPNN is built for observation, research, and resilience.

In a fragmented or degraded internet, understanding how networks behave becomes critical.

DPNN is designed for that.

