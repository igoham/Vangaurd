import logging

from nmap import PortScanner
from ipaddress import IPv4Address
from typing import Union
from datetime import datetime

import config
from scanjobs import AmassScanJob
from plugins.output import *


class CustomScan:
    def __init__(self):
        self._port_mappings = {"http": {"ports":[80,443,8080, 8081], "function": self.enum_http}}

    def enum_http(self, host, ports):
        """
        Preforms HTTP enum scan on a list of ports
        """
        # TODO push to ES
        logging.info(f"Preforming http enum on {host}")
        resp = self.scanner.scan(hosts=host, arguments=f"-sV --script=http-enum -p {','.join([str(p) for p in ports])}")
        logging.info(f"scan of {host} took: {resp.get('nmap').get('scanstats').get('elapsed')}")
        return resp.get("scan").get(host).get("tcp")


class Scanner(CustomScan):
    _intense = False
    _development = False
    _configuration_options = {
        "scanner_output": {
            "elastic": {"es_index": None, "es_host": None, "es_port": 9200, "es_password": None, "es_username": None,
                        "setup": ElasticWrapper.setup},
            "pubsub": False
        }
    }

    def __init__(self):
        self.scanner = PortScanner()
        self.config = {}
        self._load_config()

    @staticmethod
    def _ipv4(host) -> bool:
        try:
            IPv4Address(host)
            return True
        except:
            return False

    @staticmethod
    def _create_documents(host, scan_time, result, domain):
        """
        Creates a list of port documents that are formatted for ES indexing
        """
        return_list = []
        for port, scan_result in result.items():
            return_list.append({
                "timestmap": scan_time,
                "ports": result,
                "ip": host,
                "domain": domain,
                "port": port,
                "scan": scan_result
            })
        return return_list

    def _load_config(self) -> None:
        """
        Checks which plugins we have enabled via environment variables

        Sets self.output which will have a method named "submit_document" that accepts a json payload to send to the
        output plugin
        """
        for setting, options in self._configuration_options.items():
            val = config.__getattribute__(setting)
            if val in self._configuration_options.get(setting):
                conf = {"type": val}
                for sub_setting in options.get(val):
                    try:
                        conf[sub_setting] = config.__getattribute__(sub_setting)
                    except AttributeError:
                        logging.error(f"failed to get setting value from config file '{sub_setting}' due to missing value")
                        conf[sub_setting] = options[val].get(sub_setting)
            self.config[setting] = conf
            self.output = conf['setup'](conf=conf)

    def _run_intense_scan(self, result):
        scan = result.get("scan")
        if not scan:
            return

        for host, scan_res in scan.items():
            port_dict = scan_res.get("tcp")
            if not port_dict:
                return
            for scan_type, bundle in self._port_mappings.items():
                ports_found = []
                for port, res in port_dict.items():
                    if res.get("state") != "open":
                        continue
                    if port in bundle.get("ports"):
                        ports_found.append(port)
                func = bundle.get("function")
                func(host, ports_found)

    def _probe_host(self, host):
        """
        Sends the fast probe to the host to find open ports
        """
        resp = self.scanner.scan(hosts=host, arguments="-Pn -sT -T 4 --top-ports=5000")
        # Todo finish get ports function to dnyamic pull only list of ports for the single host
        try:
            tcp = resp.get("scan").get(host).get("tcp")
        except AttributeError:
            return None
        else:
            if tcp:
                ports_found = [k for k, v in tcp.items() if v.get("state") == "open"]
                return ports_found
        return None

    def service_scan(self, host, ports):
        """
        Vanilla service scan from nmap
        """
        try:
            resp = self.scanner.scan(hosts=host, arguments=f"-sV -sC -p {','.join([str(p) for p in ports])}")
        except Exception as e:
            logging.error(f"Failed to run service scan for {host} on {ports} due to {e}")
            return None
        else:
            logging.info(f"scan of {host} took: {resp.get('nmap').get('scanstats').get('elapsed')}")
            try:
                tcp_responses = resp.get("scan").get(host).get("tcp")
            except AttributeError:
                logging.error(f"No scan response found for {host}")
                return None
            else:
                return tcp_responses

    def _scan(self, host):
        """
        Scan the Address
        :param host:
        :return:
        """
        logging.info(f"Scanning {host}")
        if self._development:
            resp = self.scanner.scan(hosts=host, arguments="--unprivileged -sV -sC -Pn --top-ports=50")
        else:
            resp = self.scanner.scan(hosts=host, arguments="-sV -sC -Pn -p-")
        if self._intense is True:
            try:
                self._run_intense_scan(result=resp)
            except Exception as e:
                logging.error(f"Failed to run intense scan for {host} due to {e}")
        logging.info(f"scan of {host} took: {resp.get('nmap').get('scanstats').get('elapsed')}")
        return resp.get("scan").get(host).get("tcp")

    def scan_amass_job(self, job: AmassScanJob):
        """
        Accepts an amass result json dict and pushes the data to ES
        """
        scan_time = datetime.now()
        scan_results = []

        for addr in job.__iter__():
            if self._ipv4(addr):
                try:
                    ports = self._probe_host(host=addr)
                except Exception as e:
                    logging.error(f"Failed to scan ip {addr} due to {e}")
                    continue
                else:
                    if ports is None:
                        logging.info(f"Found no result for {addr}")
                        continue

                    result = self.service_scan(host=addr, ports=ports)
                    if result is None:
                        logging.error(f"No response from service scan on [{job.name}]{addr} for ports {ports}")
                        continue
                    documents = self._create_documents(addr, scan_time, result, job.name)
                    for doc in documents:
                        try:
                            self.output.submit_document(document=doc)
                        except Exception as e:
                            logging.info(f"Failed to send doc {doc} to es due to {e}")
                    scan_results.append(result)

            else:
                logging.info(f"Skipping {addr}) as it is not IPv4")
        else:
            logging.error("Amass scan dict didn't have addresses")

    def scanable(self, host: Union[str, IPv4Address]) -> bool:
        """
        Checks if we are allowed to scan this IP
        :param host:
        :return: bool
        """
        # TODO determine internal bad ranges to scan
        if isinstance(host, IPv4Address) is False:
            try:
                host = IPv4Address(host)
            except Exception as e:
                print(e)
                return False

        if host.is_private:
            return False
        return True

    def scan(self, scan_job: object):
        if scan_job.type == "amass":
            logging.info("Starting to scan job with 'amass' type")
            self.scan_amass_job(scan_job)
        else:
            self._scan(scan_job)


def main():
    scan = Scanner()
    scan._probe_host(host="dls.clikcup.com")


if __name__ == '__main__':
    main()