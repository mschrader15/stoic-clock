import requests
import threading
import time
import logging
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=os.path.join(ROOT, 'api-error_log.txt'), filemode="a+", )


class SettingsQuery(object):
    # """ Threading example class
    # The run() method will be started and it will run in the background
    # until the application exits.
    # """
    def __init__(self, interval, website, clock_id):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        self.settings = None
        self.website = website
        self.clock_id = clock_id

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        # global settings_dict
        while True:
            try:
                r = requests.get(self.website + self.clock_id)
                self.settings = r.json()
            except Exception:
                logging.exception("Exception occurred")
            # print("thread loop settings ", self.settings)
            time.sleep(self.interval)
