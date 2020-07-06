import time
from api import SettingsQuery
from basic import Clock
WEBSITE = 'http://0.0.0.0:5000/api/stoic-clock/'
CLOCK_ID = 'AAB'

if __name__ == "__main__":

    settings = SettingsQuery(interval=60, clock_id=CLOCK_ID, website=WEBSITE)

    clock = Clock()
    clock.main(cathode_poison_method='wave', settings=settings)

    # while True:
    #
    #     print("main loop settings ", settings.settings)
    #
    #     time.sleep(30)
    #
