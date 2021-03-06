
import unittest

from dsatest.bench import bench
from dsatest.tests.helpers import up_and_wait

@unittest.skipIf(not bench.links, "test requires at least 1 link")
class TestBridge(unittest.TestCase):

    def test_bridge_ping_all_interfaces_bridged(self):
        bridge = bench.target.add_bridge("br0")
        bridge.up()

        # setup: add all target interfaces within the Bridge
        bridge.add_address("192.168.10.1/24")
        for link in bench.links:
            link.host_if.flush_addresses()
            bridge.add_interface(link.target_if)
            up_and_wait(link)

        # test: make all host interfaces ping the bridge IP
        for i, link in enumerate(bench.links, start=2):
            host_addr = "192.168.10.{}/24".format(str(i))
            link.host_if.add_address(host_addr)

            """
            No deadline, since we need the bridge to learn our MAC address first
            """
            link.host_if.ping("192.168.10.1", count=1)
            link.host_if.flush_addresses()

        # tearDown: remove interfaces from the bridge, then delete it
        for link in bench.links:
            bridge.del_interface(link.target_if)
            link.host_if.down()
            link.target_if.down()
        bridge.down()
        bench.target.del_bridge(bridge)


    def test_bridge_ping_one_bridge_per_interface(self):
        bridges = []
        for i, link in enumerate(bench.links):
            bridge = bench.target.add_bridge("br{}".format(i))
            bridges.append(bridge)
            bridge.add_address("192.168.{}.1/24".format(str(10 + i)))
            bridge.add_interface(link.target_if)
            up_and_wait([bridge, link.host_if])

        for i, link in enumerate(bench.links):
            host_addr = "192.168.{}.2/24".format(str(10 + i))
            link.host_if.flush_addresses()
            link.host_if.add_address(host_addr)
            link.host_if.ping("192.168.{}.1".format(str(10 + i)), count=1, deadline=1)
            link.host_if.flush_addresses()

        for i, link in enumerate(bench.links):
            bridge = bridges[i]
            bridge.del_interface(link.target_if)
            bridge.down()
            bench.target.del_bridge(bridge)
