# import RPi.GPIO as GPIO
import time
from datetime import datetime, timedelta
import random

# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)

nixie_dict = {
    1: {'pins': [35, 36, 37, 38],
        'num_map': {0: 5, 1: 0, 2: 4, 3: 8, 4: 12, 5: 2, 6: 6, 7: 10, 8: 14, 9: 1}
        },
    2: {'pins': [15, 16, 18, 22],
        'num_map': {0: 9, 1: 0, 2: 8, 3: 4, 4: 12, 5: 2, 6: 10, 7: 6, 8: 14, 9: 1}
        },
    3: {'pins': [40, 19, 21, 23],
        'num_map': {0: 6, 1: 0, 2: 4, 3: 1, 4: 5, 5: 8, 6: 15, 7: 9, 8: 13, 9: 2},
        },
    4: {'pins': [24, 26, 3, 5],
        'num_map': {0: 3, 1: 0, 2: 2, 3: 8, 4: 10, 5: 4, 6: 6, 7: 12, 8: 14, 9: 1},
        },
    5: {'pins': [29, 31, 32, 33],
        'num_map': {0: 12, 1: 0, 2: 8, 3: 2, 4: 10, 5: 1, 6: 9, 7: 3, 8: 11, 9: 4},
        },
    6: {'pins': [7, 8, 12, 13],
        'num_map': {0: 5, 1: 0, 2: 4, 3: 8, 4: 12, 5: 2, 6: 6, 7: 10, 8: 14, 9: 1},
        },
}


class Clock:

    def __init__(self):

        self.nixie_dict = nixie_dict
        self.settings = {}
        self.last_hour = datetime.now().hour
        self.anti_poisoning = False
        self.rand_sec = random.randint(0, 3600)
        self.last_death_display_time = datetime.now()
        self.death_displayed = False
        self.now = datetime.now()
        self.nixie_state = {i: 0 for i in range(1, 7)}

        # for tube_num in self.nixie_dict.keys():
        #     GPIO.setup(self.nixie_dict[tube_num]['pins'], GPIO.OUT)

    def output_num(self, nixie_tube, number):
        pins = self.nixie_dict[nixie_tube]['pins']
        write_num = self.nixie_dict[nixie_tube]['num_map'][int(number)] if number != 'X' else 15
        binary = '{0:04b}'.format(write_num)
        # out_list = [GPIO.HIGH if int(bit) else GPIO.LOW for bit in binary]
        print(nixie_tube, number)
        # GPIO.output(pins, out_list)
        self.nixie_state[nixie_tube] = int(number) if number != 'X' else 0

    def main(self, cathode_poison_method, settings):
        if cathode_poison_method == "wave":
            anti_poison_func = self.anti_cathode_poison_wave
        elif cathode_poison_method == "slot":
            anti_poison_func = self.anti_cathode_poison_slot
        else:
            anti_poison_func = self.anti_cathode_poison
        while True:
            t0 = time.time()
            # Handle the settings:
            settings_error = self.settings_manager(settings=settings.settings)
            display_time = self.death_display(settings_error)
            seconds_display = self.settings['seconds_display'] if not settings_error else True
            twenty_four_hour = self.settings['twenty_four_hour'] if not settings_error else True
            offset = self.settings['time_offset'] if not settings_error else '+0'
            self.now = self.offset_manager(offset)
            self.basic_time(seconds=seconds_display,
                            twenty_four=twenty_four_hour,
                            display_time=display_time,
                            offset=offset)
            poisoning_ran = self.poisoning_manager(poison_func=anti_poison_func)
            if not poisoning_ran:
                sleep_time = max(1e-6, 1 - (time.time() - t0))
                time.sleep(sleep_time)

    def offset_manager(self, offset):
        offset_method = offset[0]
        if offset_method == '+':
            return datetime.now() + timedelta(hours=int(offset[1:]))
        else:
            return datetime.now() - timedelta(hours=int(offset[1:]))

    def death_display(self, settings_error):
        if not settings_error:
            now = self.now
            time_int = now.hour * 60 + now.minute
            if (time_int >= self.settings['low_range']) and (time_int <= self.settings['high_range']):
                if self.death_displayed:
                    seconds = (now - self.last_death_display_time).seconds
                    if seconds > self.settings['display_duration'] and (self.settings['display_interval'] > 0):
                        self.death_displayed = False
                        self.last_death_display_time = now
                        return True
                    else:
                        return False
                else:
                    interval = (now - self.last_death_display_time).seconds
                    if interval >= self.settings['display_interval']:
                        for i, num in enumerate(str(self.settings['days_till_death'])):
                            self.output_num(i + 2, num)
                        self.output_num(1, 'X')
                        self.death_displayed = True
                        self.last_death_display_time = now
                        return False
                    return True
        return True

    def basic_time(self, seconds=True, twenty_four=True, display_time=True, offset='+0'):
        now = self.now
        hour = now.hour
        minute = now.minute
        sec = now.second
        str_time = []
        if display_time:
            if seconds:
                start_ind = 1
            else:
                hour = 'XX'  # 15 is a mask for off
                minute = now.hour
                sec = now.minute
                start_ind = 1
            if not twenty_four:
                if int(hour) > 12:
                    if seconds:
                        hour = 'X' + str(int(hour) - 12)
                    else:
                        minute = 'X' + str(int(minute) - 12)
            for i, time_chunk in enumerate([hour, minute, sec]):
                if len(str(time_chunk)) < 2:
                    str_time.append("0" + str(time_chunk))
                else:
                    str_time.append(str(time_chunk))
            time_string = "".join(str_time)
            for i, num in enumerate(time_string):
                self.output_num(nixie_tube=i + start_ind, number=num)

    def poisoning_manager(self, poison_func, ):
        if self.now.hour != self.last_hour:
            self.anti_poisoning = False
            self.last_hour = self.now.hour
            return False
        if ((self.now.minute * 60 + self.now.second) >= self.rand_sec) and not self.anti_poisoning:
            poison_func()
            # print(f"Anti_poisoning ran @ {hour}:{sec}. Random number was {self.rand_sec}")
            self.rand_sec = random.randint(0, 3600)
            self.anti_poisoning = True
            return True

    def settings_manager(self, settings):
        settings_error = True
        try:
            if settings is not None:
                self.settings['days_till_death'] = self.get_days_till_death(settings['date_of_birth'],
                                                                            settings['death_age']) \
                    if settings['death_display'] else None
                self.settings['death_display'] = settings['death_display']
                self.settings['display_duration'] = int(settings['display_duration'])
                self.settings['display_interval'] = int(settings['display_interval'])
                self.settings['twenty_four_hour'] = settings['twenty_four_hour']
                self.settings['seconds_display'] = settings['seconds_display']
                self.settings['time_offset'] = settings['time_offset']
                times = settings['time_range'].split("-")
                time_range = []
                for local_time in times:
                    time_range.append(int(local_time.split(':')[0]) * 60 + int(local_time.split(':')[1]))
                self.settings['low_range'] = time_range[0]
                self.settings['high_range'] = time_range[1]
                settings_error = False
                return settings_error
            settings_error = True
            return settings_error
        except AttributeError:
            return settings_error

    @staticmethod
    def get_days_till_death(birth_day_string, death_age):
        dob = datetime.strptime(birth_day_string, "%m/%d/%Y")
        end_date_string = dob.year + int(float(death_age))
        end_date_string = "/".join(birth_day_string.split('/')[:2] + [str(end_date_string)])
        end = datetime.strptime(end_date_string, "%m/%d/%Y")
        diff = end - datetime.now()
        return diff.days

    def anti_cathode_poison(self):
        last_value = [0] * 6
        k = 0
        while last_value[-1] < 9:
            k += 1
            for i in range(1, 7):
                for j in range(0, 3):
                    num = last_value[i - 1] + j
                    num = num if num < 10 else 15
                    self.output_num(nixie_tube=i, number=num)
                    time.sleep(0.3)
                last_value[i - 1] += j
        last_value = [0] * 6
        while last_value[-1] < 9:
            k += 1
            for i in range(1, 7):
                local_i = 7 - i
                for j in range(0, 3):
                    num = last_value[local_i - 1] + j
                    num = num if num < 10 else 15
                    self.output_num(nixie_tube=i, number=num)
                    time.sleep(0.3)
                last_value[local_i - 1] += j

    def anti_cathode_poison_wave(self):
        for i in range(0, 10):
            if i % 2 > 0:
                func = lambda x: 7 - x
            else:
                func = lambda x: x
            for tube_num in range(1, 7):
                local_tube_num = func(tube_num)
                self.output_num(nixie_tube=local_tube_num, number=i)
                time.sleep(0.05)
        for i in range(0, 10):
            loc_i = 9 - i
            if loc_i % 2 > 0:
                func = lambda x: 7 - x
            else:
                func = lambda x: x
            for tube_num in range(1, 7):
                local_tube_num = func(tube_num)
                self.output_num(nixie_tube=local_tube_num, number=i)
                time.sleep(0.05)

    def anti_cathode_poison_slot(self):

        rand_list = [random.randint(20, 50) for i in range(6)]
        local_count = [0] * 6
        master_count = 0
        done = [False] * 6
        while not all(done):
            for nixie_tube in range(1, 7):
                if local_count[nixie_tube-1] < rand_list[nixie_tube-1]:
                    try:
                        display_num = self.nixie_state[nixie_tube] + 1
                    except TypeError:
                        display_num = 0
                    display_num = display_num if display_num < 10 else 0
                    self.output_num(nixie_tube, display_num)
                    local_count[nixie_tube - 1] += 1
                else:
                    done[nixie_tube - 1] = True
            time.sleep(0.05 * (master_count+1)**(1/3))
            master_count += 1


if __name__ == "__main__":
    Clock().anti_cathode_poison_slot()
