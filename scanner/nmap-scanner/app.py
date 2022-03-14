from flask import Flask
from scanner import Scanner
from threading import Thread
from time import sleep
import logging
import sys


from plugins.input import *
import config


# Declare logging configurations
logging.basicConfig(filename='nmap.log', encoding='utf-8', level=logging.DEBUG)
root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


class ScanManager(Flask):
    _scan_threads = {}
    _configuration_options = {
        "scanner_input": {
            "rabbitmq": {"host": None, "port": 5672, "queue_names": ["amass_jobs"], "setup": RabbitMQWrapper.setup},
            "http": False
        }
    }

    def __init__(self, name):
        super().__init__(name)
        self._load_config()
        for i in range(4):
            logging.info(f"Starting Scanning thread {i}")
            self._scan_threads[i] = Thread(target=self._check_for_jobs_loop)
            self._scan_threads[i].setDaemon(True)
            self._scan_threads[i].start()

    def _load_config(self) -> None:
        # TODO only load a single config
        for setting, options in self._configuration_options.items():
            val = config.__getattribute__(setting)
            if val in self._configuration_options.get(setting):
                conf = {"type": val}
                for sub_setting in options.get(val):
                    try:
                        conf[sub_setting] = config.__getattribute__(sub_setting)
                    except AttributeError:
                        logging.error(
                            f"failed to get setting value from config file '{sub_setting}' due to missing value")
                        conf[sub_setting] = options[val].get(sub_setting)
            self.config[setting] = conf
            self.input = conf['setup'](conf=conf)

    def _check_for_jobs_loop(self):
        scanner = Scanner()
        while True:
            try:
                scan_job = self.input.check_for_message()
            except Exception as e:
                logging.error(f"Failed to get a scan from input type '{self.input.type}' due to {e}")
                # TODO sleep backoff?
                sleep(30)
            else:
                if scan_job is None:
                    logging.info("No scan jobs found")
                    sleep(10)
                else:
                    scanner.scan(scan_job)


app = ScanManager(__name__)
app.scanner = Scanner()


from views import *
