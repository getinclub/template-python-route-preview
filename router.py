"""Offline route-table preview. No sockets, OS routes or network traffic."""
from ipaddress import IPv4Address, IPv4Network
import re


def _validated(destination, routes):
    if not isinstance(destination, str):
        raise ValueError("destination must be a dotted-decimal IPv4 string")
    try:
        address = IPv4Address(destination)
    except ValueError as exc:
        raise ValueError("invalid IPv4 destination") from exc
    if not isinstance(routes, list):
        raise ValueError("routes must be a list")
    parsed, ids = [], set()
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("each route must be a dictionary")
        ident, cidr, metric = route.get("id"), route.get("cidr"), route.get("metric")
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            raise ValueError("route IDs must be unique nonempty strings")
        if type(metric) is not int or metric < 0:
            raise ValueError("metric must be a nonnegative integer, not bool")
        if not isinstance(cidr, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}/(?:0|[1-9][0-9]?)", cidr):
            raise ValueError("CIDR must use dotted IPv4 and a decimal prefix length")
        try:
            network = IPv4Network(cidr, strict=True)
        except ValueError as exc:
            raise ValueError("CIDR must be IPv4 with zero host bits") from exc
        ids.add(ident)
        parsed.append((route, network))
    return address, parsed


def select_route(destination, routes):
    """Return the selected route ID, or None; see README for complete policy."""
    address, parsed = _validated(destination, routes)
    # The preview currently stops as soon as any row matches.
    for route, network in parsed:
        if address in network:
            return route["id"]
    return None
