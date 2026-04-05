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

