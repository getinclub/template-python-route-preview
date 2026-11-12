# The Route Preview That Sent Traffic to the Default Gateway

A support engineer previews a route to `10.42.7.19`. The tool says `internet-edge`, although the route table contains a service-network route. No packets are sent: this is an authored, deterministic Python exercise.

## Reproduce

Use Python 3.12 or later. No third-party packages or network account are needed.

```sh
python monitor.py
python -m unittest -v
```

The starter monitor exits 1 with a preview mismatch; the starter test suite is intentionally red. Fix only `select_route()` in `router.py`. Keep validation and the public API. Do not change fixtures or tests to manufacture a pass. Open a PR against `main` when the suite and monitor pass.

## Selection contract

`select_route(destination, routes)` returns a route's `id`, or `None` if no route covers the destination.

1. Consider only IPv4 networks containing the destination, including network and broadcast addresses in this mathematical preview.
2. Prefer the longest matching CIDR prefix, even if a broader route has a cheaper metric.
3. Among equally specific matches, prefer the lowest metric, then the lexicographically smallest route ID (Python string order).
4. Never depend on table order. Do not mutate the table or its records. No state may leak between calls.
5. Validate the **entire input** before returning, including unrelated rows. Raise `ValueError` for invalid input.

The destination must be a dotted-decimal IPv4 string accepted by Python's `IPv4Address`. Routes must be a list of dictionaries with required keys `id`, `cidr` and `metric`. Each `id` must be a unique, nonblank string; `cidr` must be a string; `metric` must be a nonnegative integer, excluding booleans. CIDR must be dotted-decimal IPv4 followed by `/` and a canonical decimal prefix length 0–32; network host bits must be zero. Dotted netmasks, host-only CIDRs, IPv6, and padded prefix lengths are rejected. Metrics are nonnegative Python integers, excluding booleans. Additional dictionary metadata is allowed and must remain untouched. Empty tables are valid. Nonblank IDs retain exact spelling and are not trimmed.

Use standard-library `ipaddress` helpers freely. Aim for O(n) selection work for n routes; no trie or routing daemon is required. The provided validator parses the whole table in O(n) space. Do not claim O(1) space for the complete function.

## Acceptance

The supplied replay must select `service` / `service-net`. Tests also cover `/0`, `/32`, non-octet prefixes, boundaries, tied metrics, permutations, large tables, invalid trailing rows and input preservation. Explain why your ranking is independent of input order.

## Scope

This policy is deliberately simplified. It does not implement BGP, administrative distance, ECMP, policy routing, link state, IPv6, or reachability. Passing does not certify real firewall or router configuration. It makes no OS, cloud or network changes.
