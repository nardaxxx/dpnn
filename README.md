DPNN — Distributed Privacy Node Network
DNS answers are no longer universal — they depend on who is asking and from where.
DPNN lets you see the internet as it appears from other networks.
The problem
The same domain does not resolve the same way everywhere.
What you see depends on where you are.
Your country, your ISP, your network — CDN geolocation, filtering rules,
split-horizon configurations — all shape the answer you receive.
The same domain resolves differently, or not at all, depending on who is asking.
DPNN is a response to that fragmentation.
What DPNN does
DPNN lets you query DNS through a human node in another network.
That human node resolves using their own system DNS — exactly as they would for themselves.
You receive the answer their network sees.
Not a public resolver. Not a VPN. Not a proxy. Not centralized DoH.
A network of human nodes lending their native DNS context to each other.
Human node — a node run by a real person on a real network: home, mobile, or office.
Not an automated server in a datacenter. Your connection becomes an authentic observation point.
You choose the country. The human node resolves. You get their view.
Use cases
Compare DNS resolution across countries and ISPs
Detect filtering or blocking applied by a specific network
Observe CDN geolocation behavior from different vantage points
Analyze split-horizon DNS differences
Debug region-specific DNS issues
How it works
your browser
     ↓  DNS query (DoH)
DPNN Resolver  127.0.0.1:53535
     ↓  DPNN protocol (TCP/JSON)
human node in chosen country
     ↓  system DNS query
authoritative nameserver
     ↑  answer
human node
     ↑  answer
DPNN Resolver
     ↑  DNS answer
your browser
Node (dpnn_node.py) — runs on any machine. Accepts DNS queries from peers
and resolves them using the local system DNS. No special configuration needed.
The network context of the machine is what makes the answer authentic.
Resolver (dpnn_resolver.py) — runs locally. Listens on 127.0.0.1:53535
as a DNS over HTTPS (DoH) endpoint. Set it as your browser DNS once — done.
What makes DPNN different
Feature
DPNN
Public DNS
VPN
Uses remote DNS context
✔
✖
✔
Uses real user networks
✔
✖
✖
Centralized
✖
✔
✔
No single point to block
✔
✖
✖
Quick start
Install
git clone https://github.com/YOUR_USER/dpnn.git
cd dpnn
pip3 install dnslib dnspython
Python 3.9+. No other dependencies. No root required.
Configure
export DPNN_REGISTRY_URLS="https://raw.githubusercontent.com/YOUR_USER/dpnn-peers/main/peers.json"
See available countries
python3 dpnn_resolver.py --list
Start the resolver
python3 dpnn_resolver.py --country DE
Set your browser DNS
Chrome / Brave:
Settings → Privacy → Security → Use secure DNS → Custom:
http://127.0.0.1:53535/dns-query
Firefox:
Settings → Privacy → DNS over HTTPS → Custom:
http://127.0.0.1:53535/dns-query
Test immediately (without changing browser settings)
curl 'http://127.0.0.1:53535/dns-query?name=example.com&type=A'
Running a human node
export GITHUB_TOKEN="your_token"
export DPNN_REPO_OWNER="registry_github_user"
export DPNN_REPO_NAME="dpnn-peers"

python3 dpnn_node.py run
Your machine registers in the peer list with country, ASN, and org metadata.
You resolve queries using your own system DNS — exactly as you do for yourself.
Your network perspective becomes available to the network.
Threat model
DPNN does not guarantee:
anonymity of the querier
censorship resistance
correctness of peer responses
trustless operation
A human node may return incorrect data, misrepresent its location,
or operate on a filtered or modified network.
DPNN is designed for observation and comparison, not blind trust.
DPNN is not about correctness. It is about observation.
Human nodes can see your queries. There is no built-in anonymization layer.
DoH layer
The local resolver implements RFC 8484 (DNS over HTTPS):
Media type: application/dns-message
Supports POST (default) and GET
Preserves full DNS response structure
Explicit error signaling — no silent fallback to external DNS
Legal and research context
DPNN queries publicly available DNS information through human nodes.
It does not intercept traffic, bypass firewalls, or hide connections.
This is the same model used by RIPE Atlas — a distributed network of
volunteer probes measuring real DNS behavior from real networks worldwide,
funded by European public institutions — and by CAIDA, used by academic
and government researchers globally.
Participation as a node is voluntary and explicit.
Status
DPNN v1.0 is released and functional.
The node and resolver work. The protocol is defined. The network is open.
Join as a user, run a human node, or contribute to the next stage.
Roadmap
Stage 1 — Now
[x] Functional node and resolver
[x] Peer exchange and metadata (country, ASN, org)
[x] Local DoH resolver, no root required
[x] Multi-source registry, parallel fetch
Stage 2 — Short term
[ ] Local peer cache — works even when all registries are unreachable
[ ] --verify mode — cross-check across multiple peers, flag divergences
[ ] Connection type classification: residential / mobile / VPS / unknown
[ ] Windows build
Stage 3 — Mid term
[ ] Immutable peer registry anchored on a public blockchain
[ ] Signed peer identities and metadata
[ ] Multi-source bootstrap with no single point of control
Stage 4 — Long term
[ ] Node compensation — peers earn micropayments per query via smart contract
[ ] Full decentralization: no GitHub, no central server, no owner
[ ] The registry lives on-chain. The network runs itself.
Philosophy
DPNN does not try to fix DNS.
It exposes what DNS has become.
Contributing
Open an issue or pull request.
Running a human node is already a contribution — every new network perspective adds value.
Areas of interest: networking, DNS internals, distributed systems,
blockchain/smart contracts, security and trust models.
License
DPNN Network License — v1.0
You are free to use, copy, share, and distribute this software.
To participate in the DPNN network you must be registered in the official
DPNN registry on Decentraland/Ethereum and pay the network fee.
The only official registry is the DPNN smart contract deployed on Ethereum.
No third party can collect fees on behalf of DPNN.
The code is free. The network has one door. That door is on the blockchain.
See LICENSE.
