import json
import logging

from ipaddress import IPv4Network, AddressValueError
from typing import Generator


class AmassScanJob(object):
    """
    Scan job for a single response line from the Amass output file
    """
    network = None
    type = "amass"
    job_metadata_index_name = "scan_jobs"
    scan_results_index_name = "nmap_port_scans"

    def __init__(self, data):
        for k,v in data.items():
            self.__setattr__(k, v)

    def __len__(self):
        if self.network is None:
            return 0
        else:
            return self.network.num_addresses

    def __iter__(self) -> Generator:
        return (n.get("ip") for n in self.addresses)

    def _load(self, network):
        try:
            self.network = IPv4Network(network)
        except AddressValueError:
            logging.error(f"Failed to load network: {network} into scan job")

    def to_json(self) -> dict:
        return {
            "type": self.type,
            "metadata_index": self.job_metadata_index_name,
            "results_index": self.scan_results_index_name,
            "ips": self.__iter__(),
            "class": AmassScanJob
        }

if __name__ == '__main__':
    t = """{"name":"world65.runescape.com","domain":"runescape.com","addresses":[{"ip":"8.26.41.166","cidr":"8.26.41.0/24","asn":44521,"desc":"JAGEX-AS"}],"tag":"api","sources":["BufferOver"]}"""
    t = json.loads(t)
    a = AmassScanJob(t)
    x=1