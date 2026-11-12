import copy
import itertools
import unittest
from router import select_route


def r(ident, cidr, metric=0):
    return {"id": ident, "cidr": cidr, "metric": metric}


class RouteTests(unittest.TestCase):
    def test_monitor_regression(self):
        from monitor import ROUTES
        self.assertEqual(select_route("10.42.7.19", ROUTES), "service")

    def test_prefix_beats_metric(self):
        self.assertEqual(select_route("10.1.2.3", [r("broad", "10.0.0.0/8", 0), r("specific", "10.1.2.0/24", 999)]), "specific")

    def test_metric_before_id(self):
        self.assertEqual(select_route("10.1.2.3", [r("a", "10.0.0.0/8", 9), r("z", "10.0.0.0/8", 1)]), "z")

    def test_id_final_tie(self):
        self.assertEqual(select_route("10.1.2.3", [r("z", "10.0.0.0/8", 1), r("a", "10.0.0.0/8", 1)]), "a")

    def test_permutations(self):
        table = [r("default", "0.0.0.0/0"), r("wide", "10.0.0.0/8"), r("z", "10.1.0.0/16", 3), r("a", "10.1.0.0/16", 3)]
        for perm in itertools.permutations(table):
            self.assertEqual(select_route("10.1.2.3", list(perm)), "a")

    def test_nonmatching_specific_does_not_win(self):
        self.assertEqual(select_route("10.1.2.3", [r("other", "11.1.2.3/32"), r("default", "0.0.0.0/0")]), "default")

    def test_no_match(self):
        self.assertIsNone(select_route("10.1.2.3", [r("other", "11.0.0.0/8")]))

    def test_empty(self):
        self.assertIsNone(select_route("0.0.0.0", []))

    def test_host_exact(self):
        self.assertEqual(select_route("10.1.2.3", [r("net", "10.1.2.0/24"), r("host", "10.1.2.3/32", 999)]), "host")

    def test_host_neighbor(self):
        self.assertEqual(select_route("10.1.2.4", [r("net", "10.1.2.0/24"), r("host", "10.1.2.3/32")]), "net")

    def test_non_octet_17_inside(self):
        self.assertEqual(select_route("10.42.200.1", [r("wide", "10.42.0.0/16"), r("narrow", "10.42.128.0/17")]), "narrow")

    def test_non_octet_17_outside(self):
        self.assertEqual(select_route("10.42.127.255", [r("narrow", "10.42.128.0/17"), r("wide", "10.42.0.0/16")]), "wide")

    def test_slash31_endpoints(self):
        for address in ["192.0.2.10", "192.0.2.11"]:
            self.assertEqual(select_route(address, [r("wide", "192.0.2.0/24"), r("pair", "192.0.2.10/31")]), "pair")

    def test_network_and_broadcast(self):
        for address in ["192.0.2.0", "192.0.2.255"]:
            self.assertEqual(select_route(address, [r("default", "0.0.0.0/0"), r("subnet", "192.0.2.0/24")]), "subnet")

    def test_ipv4_extremes(self):
        for address in ["0.0.0.0", "255.255.255.255"]:
            self.assertEqual(select_route(address, [r("default", "0.0.0.0/0")]), "default")

    def test_lexical_id_order(self):
        self.assertEqual(select_route("1.2.3.4", [r("route-2", "0.0.0.0/0"), r("route-10", "0.0.0.0/0")]), "route-10")

    def test_huge_metrics(self):
        self.assertEqual(select_route("1.2.3.4", [r("a", "0.0.0.0/0", 10**100+1), r("z", "0.0.0.0/0", 10**100)]), "z")

    def test_nonmutation(self):
        table=[r("z", "0.0.0.0/0"),r("a", "10.0.0.0/8")]
        table[0]["metadata"]={"notes":["keep"]}
        before=copy.deepcopy(table)
        select_route("10.0.0.1",table)
        self.assertEqual(table,before)

    def test_independent_calls(self):
        self.assertEqual(select_route("10.0.0.1",[r("a","10.0.0.0/8")]),"a")
        self.assertIsNone(select_route("10.0.0.1",[]))
        self.assertEqual(select_route("10.0.0.1",[r("b","0.0.0.0/0")]),"b")

    def test_large_table(self):
        table=[r(f"n{i:05}",f"10.{i//256}.{i%256}.0/24",i) for i in range(10000)]
        table.insert(0,r("default","0.0.0.0/0"))
        self.assertEqual(select_route("10.39.15.77",table),"n09999")

    def test_equal_routes_distinct_ids_allowed(self):
        self.assertEqual(select_route("10.0.0.1",[r("b","10.0.0.0/8"),r("a","10.0.0.0/8")]),"a")

    def test_id_not_trimmed(self):
        self.assertEqual(select_route("10.0.0.1",[r(" a ","10.0.0.0/8")])," a ")


def invalid_test(destination, routes):
    def test(self):
        with self.assertRaises(ValueError):
            select_route(destination,routes)
    return test

BAD_CASES = {
    "destination_integer": (123, []),
    "destination_ipv6": ("::1", []),
    "destination_cidr": ("10.0.0.1/32", []),
    "destination_bad_octet": ("999.0.0.1", []),
    "destination_leading_zero": ("010.0.0.1", []),
    "routes_none": ("1.2.3.4", None),
    "routes_tuple": ("1.2.3.4", ()),
    "record_not_dict": ("1.2.3.4", [1]),
    "missing_id": ("1.2.3.4", [{"cidr":"0.0.0.0/0","metric":0}]),
    "blank_id": ("1.2.3.4", [r("  ","0.0.0.0/0")]),
    "duplicate_id": ("1.2.3.4", [r("x","0.0.0.0/0"),r("x","10.0.0.0/8")]),
    "missing_metric": ("1.2.3.4", [{"id":"x","cidr":"0.0.0.0/0"}]),
    "negative_metric": ("1.2.3.4", [r("x","0.0.0.0/0",-1)]),
    "bool_metric": ("1.2.3.4", [r("x","0.0.0.0/0",True)]),
    "float_metric": ("1.2.3.4", [r("x","0.0.0.0/0",1.0)]),
    "cidr_no_prefix": ("1.2.3.4", [r("x","1.2.3.4")]),
    "cidr_host_bits": ("1.2.3.4", [r("x","10.0.0.1/8")]),
    "cidr_ipv6": ("1.2.3.4", [r("x","::/0")]),
    "cidr_too_long": ("1.2.3.4", [r("x","0.0.0.0/33")]),
    "cidr_netmask": ("1.2.3.4", [r("x","0.0.0.0/0.0.0.0")]),
    "cidr_padded_prefix": ("1.2.3.4", [r("x","0.0.0.0/00")]),
    "invalid_trailing_unmatched": ("1.2.3.4", [r("default","0.0.0.0/0"),r("bad","10.0.0.1/8")]),
}
for name,args in BAD_CASES.items():
    setattr(RouteTests,"test_invalid_"+name,invalid_test(*args))

if __name__ == "__main__":
    unittest.main()
