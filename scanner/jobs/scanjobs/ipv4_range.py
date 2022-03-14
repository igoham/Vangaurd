import logging

from ipaddress import IPv4Network, AddressValueError
from typing import Generator


class IpV4RangeScanJob(object):
    """
    Scan job that can be sent to the scan manager
    """
    network = None
    type = "range"
    _index_name = "nmap_port_scans"

    def __init__(self, network):
        self.initial_value = network
        self._load(network)

    def __len__(self):
        if self.network is None:
            return 0
        else:
            return self.network.num_addresses

    def __iter__(self) -> Generator:
        return (n for n in self.network)

    def _load(self, network):
        try:
            self.network = IPv4Network(network)
        except AddressValueError:
            logging.error(f"Failed to load network: {network} into scan job")

    def to_json(self) -> dict:
        return {
            "type": self.type,
            "initial_value": self.initial_value,
            "index": self._index_name,
            "ips": self.__iter__(),
            "class": IpV4RangeScanJob
        }
