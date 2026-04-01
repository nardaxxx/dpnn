# dpnn
Distribuited Pryvacy Node Network - P2P DNS Mesh
## What is DPNN

DPNN is an open source project that creates a distributed peer-to-peer DNS network. Every user who installs the program becomes a DNS node. Nodes connect directly to each other, forming a decentralized infrastructure that grows autonomously with every new participant.

---

## What it does today

When a user installs DPNN on their PC, that device resolves DNS queries through the distributed node network instead of the default ISP or Google DNS resolver. This reduces DNS query latency and removes direct dependency on centralized resolvers at the device level.

DPNN does not modify router configuration and does not bypass ISP-level DNS blocking. It operates at the individual device level.

---

## Why it matters

Most users never change their DNS configuration. DPNN requires zero configuration — install and run. The node starts automatically, joins the network, and begins operating immediately.

The network grows with every installation. More nodes mean lower latency, higher resilience, and broader geographic distribution.

---

## The real value: infrastructure

DPNN is not an end product. It is infrastructure.

The core innovation is building a functional P2P mesh network that works even behind CGNAT — the restrictive NAT used by most residential ISPs — using UDP hole punching and STUN protocol, the same technology behind BitTorrent and WebRTC.

Once nodes can communicate through CGNAT, the same network can carry:

- Distributed DNS resolution (Phase 1 — current)
- Distributed VPN routing (Phase 2)
- Any peer-to-peer communication layer (Phase 3)

---

## Technical architecture

**Node discovery**
New nodes download an initial peer list from a public GitHub registry. Once connected, peer exchange is fully autonomous between nodes.

**NAT traversal**
UDP hole punching + STUN protocol. Nodes behind CGNAT establish direct connections without port forwarding or VPS.

**DNS resolution**
Each node acts as a local DNS resolver for the host device. Upstream resolvers are configurable — default: Quad9, OpenDNS. No Google DNS, no Cloudflare.

**Self-healing**
Inactive nodes are removed automatically via periodic heartbeat. The network repairs itself.

**Technology stack**
Python 3.12, dnslib, pystray, Pillow, PyInstaller, UDP raw socket, STUN, GitHub API

---

## Current status

- Distributed node architecture defined
- Base node running on Linux
- Local DNS server operational
- System tray interface active
- GitHub bootstrap registry live at github.com/nardaxxx/dpnn-peers
- UDP hole punching: in development

---

## Roadmap

**3 months**
- UDP hole punching and STUN implementation
- Automatic peer exchange between nodes
- Windows EXE release

**6 months**
- Public beta
- 1,000 active nodes target
- Website and documentation

**12 months**
- Stable v1.0
- VPN routing layer on existing node infrastructure
- 10,000 active nodes target

---

## Intellectual property

The combination of distributed DNS resolution over a CGNAT-traversing P2P mesh network is under evaluation for international patent filing.

---

## Author

Giovanni — network engineer, OpenWrt specialist, founder of Human Flag (humanflag.org), Swiss non-profit. Based in Ticino, Switzerland.

Contact: via GitHub

---

*DPNN — Build the network first. The rest follows.*
```
