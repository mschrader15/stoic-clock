import time
from api import SettingsQuery
from basic_noRPI import Clock
WEBSITE = 'http://10.0.0.79:5000/api/clock/'
CLOCK_ID = 'AAB'

if __name__ == "__main__":

    settings = SettingsQuery(interval=120, clock_id=CLOCK_ID, website=WEBSITE)

    clock = Clock()
    clock.main(cathode_poison_method='wave', settings=settings)

    # while True:
    #
    #     print("main loop settings ", settings.settings)
    #
    #     time.sleep(30)
    #
