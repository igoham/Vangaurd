import logging
import subprocess
import json
import os
import dns
import platform
import config
import pika
from time import perf_counter
from sys import argv
from dns import resolver

from queue import Queue
from datetime import datetime
from elastic import ElasticWrapper


class DomainRecon:
    _subdomain_file = "subdomains.txt"

    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.queue = Queue()
        self._load_subdomains()
        self.cache = {"domains": []}

    def _load_subdomains(self):
        with open(file=self._subdomain_file) as fp:
            data = fp.readlines()

        self.subdomains = [d.strip().lower() for d in data if d != ""]

    def subdomain_bruteforce(self, domain) -> str:
        found_domains = {}
        for subd in self.subdomains:
            domain_to_test = f"{subd}.{domain}"
            try:
                answer = self.resolver.query(domain_to_test, "A")
            except:
                continue
            else:
                print(f"found {domain_to_test} with {(len(answer))} - {answer}")
                ips = [str(ip) for ip in answer]
                found_domains[domain_to_test] = ips
        self.update_subdomains(subdomains=list(found_domains.keys()))

    def update_subdomains(self, subdomains: list):
        if not isinstance(subdomains, list):
            return

        for subdomain in subdomains:
            if isinstance(subdomain, str):
                if subdomain not in self.subdomains:
                    self.subdomains.append(subdomain)
        with open("test_subdomains.txt", "w") as fp:
            fp.writelines(self.subdomains)

    def preform_amass_enum(self, domain) -> str:
        """
        Returns output file name to pass to next func
        """
        start = perf_counter()
        logging.info(f"starting to scan {domain}")
        print(f"starting to scan {domain}")
        # TODO - Remove when shifting to production builds
        if platform.node() == "DESKTOP-E4O9H59":
            output_file = f'results/{"".join(domain.split(".")[:-1])}.json'
        else:
            output_file = f'/scanner/results/{"".join(domain.split(".")[:-1])}.json'
        while True:
            try:
                subprocess.Popen(["amass", "enum", "-d", domain, "-json", output_file, "-ipv4"],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE).wait()
            except Exception as e:
                logging.error(f"Failed to run amass scan against {domain} due to {e}")
            else:
                logging.info(f"completed amass can on {domain}")
                break

        logging.info(f"[Elapsed:{perf_counter() - start}] Finished scanning {domain}")
        print(f"[Elapsed:{perf_counter() - start}] Finished scanning {domain}")
        # Submit the results of the amass scan to the scan queue and post the job metadata to elastic search
        self.process_amass_enum_results(output_file)

    @staticmethod
    def send_amass_requests_to_queue(data):
        queue_name = "scan_jobs"
        logging.info(f"CONNECTING to {config.RABBIT_MQ_HOST} {config.RABBIT_MQ_PORT}")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=config.RABBIT_MQ_HOST, port=config.RABBIT_MQ_PORT))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=str.encode(json.dumps(data)))
        logging.info(f" [x] Sent '{data}' to {queue_name}")
        connection.close()

    def process_amass_enum_results(self, file):

        # TODO check file exists
        es = ElasticWrapper()
        if not os.path.exists(file):
            print(f"Unable to find amass enum result file {file}")
            logging.error(f"Unable to find amass enum result file {file}")

        with open(file, "r") as fp:
            results = fp.readlines()

        # Keep our own list up to date with all new findings
        subdomains = [".".join(domain.split(".")[:-2]) for domain in results]
        # self.update_subdomains(subdomains)

        for result in results:
            data = json.loads(result)
            if data.get("name") in self.cache['domains']:
                pass
            logging.debug(f"Starting amass scan on {data}")
            self.send_amass_requests_to_queue(data)
            logging.debug("Completed amass scan")
            data['timestmap'] = datetime.now()
            es.submit_document(index="amass_results", document=data)
            self.cache['domains'].append(data.get("name"))


def main():
    recon = DomainRecon()
    # file_name = recon.preform_amass_enum("clickup.com")
    file_name = "results/dota2.json"
    recon.process_amass_enum_results(file_name)
    # recon.subdomain_bruteforce("runelite.net")


if __name__ == '__main__':
    main()

