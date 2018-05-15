import time
import datetime
import json

import pytradfri
import requests
import logging

"""

If it's dark, nobody was home and someone is home now    -  light on

"""

logging.basicConfig(
    filename='lights.log', level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

is_dark = False
last_home = None

DAYLIGHT_API = 'http://api.sunrise-sunset.org/json'

CHECK_INTERVAL = 5  # Anyone came home within <minutes>?


def read_settings():
    with open('./settings.json') as f:
        settings = json.load(f)
    return settings


def parse_date(date_string):
    """
    Parse date string to timezone-naive datetime object.

    :param date_string: Date/time string in UTC
    :return: parsed datetime object
    """

    # tokens = date_string.split(':')
    # tokens[-2] = ''.join(tokens[-2:])
    #
    # dt = datetime.datetime.strptime(
    #     ':'.join(tokens[:-1]),
    #     '%Y-%m-%dT%H:%M:%S%z'
    # )
    dt = datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S+00:00')
    return dt


def get_daylight(latitude, longitude, apiurl=DAYLIGHT_API):
    """
    Retrieves today's daylight info from Web API
    :param apiurl: Web API URL
    :param latitude: Location coordinates
    :param longitude: Location coordinates
    :return: A tuple of datetimes for nautical twilight end (=no longer dark in the morning) and nautical twilight
        start (=start of darkness in the evening).
    """
    data = requests.get(
        apiurl,
        params={
            'lat': latitude,
            'lng': longitude,
            'formatted': 0
        }).json()
    start_dark = parse_date(data['results']['nautical_twilight_end'])
    end_dark = parse_date(data['results']['nautical_twilight_begin'])
    return start_dark, end_dark


def check_darkness(dt, latitude, longitude):
    """
    Check if it's dark in the location at the specified time.
    :param dt: Time to check
    :param lat: Location's latitude
    :param long: Location's longitude
    :return: True if it's dark, False otherwise
    """
    start_dark, end_dark = get_daylight(latitude=latitude, longitude=longitude)

    if dt < end_dark or dt > start_dark:
        return True
    return False


def read_leases(filepath, macs=[]):
    entries = []
    with open(filepath) as leases:
        entry = {}
        for line in leases:
            if line.startswith('lease'):
                if entry:
                    entries.append(entry)
                    entry = {}
                entry['ip'] = line.split()[1]
            elif line == '}':
                if entry:
                    entries.append(entry)
                    entry = {}
            if not entry:
                continue
            line = line.strip()
            if line.startswith('cltt'):
                entry['ltt'] = datetime.datetime.strptime(
                    'T'.join(line.split()[2:]),
                    '%Y/%m/%dT%H:%M:%S;')
            elif line.startswith('hardware ethernet'):
                entry['mac'] = line.split()[-1].rstrip(';')

        if entry:
            entries.append(entry)

    if macs:
        return [entry for entry in entries if entry['mac'] in macs]
    else:
        return entries


def anyone_home(dt, leases):
    """
    Is anyone just came home at this time?
    :param dt: datetime object to check
    :param leases: leases
    :return: True if anyone came back less than 5 minutes ago, False otherwise
    """
    interval = datetime.timedelta(minutes=CHECK_INTERVAL)
    for lease in leases:
        diff = dt-lease['ltt']
        if diff <= interval:
            return True
    return False


def turnon_light():
    pass


def main_loop():
    is_home_occupied = False
    settings = read_settings()

    while True:
        logging.debug('Running check loop!')
        now = datetime.datetime.utcnow()
        leases = read_leases(
            filepath=settings['leases_file'], macs=settings['macs']
        )
        if not is_home_occupied and anyone_home(now, leases):
            # Nobody was home but came home within 5 minutes ago and it's dark
            logging.info('Someone just came home!')
            is_home_occupied = True
            if check_darkness(now, settings['latitude'], settings['longitude']):
                logging.debug('And it\'s dark! Turn the light on!')
                turnon_light()
        elif is_home_occupied and not anyone_home(now, leases) and not check_darkness(
                now, settings['latitude'], settings['longitude']
        ):
            # Someone was home but nobody home now AND it's not dark
            logging.info('Assuming home is empty now')
            is_home_occupied = False
        else:
            logging.debug('Nothing happened. Sleeping...')
        time.sleep(5)


if __name__ == '__main__':
    main_loop()
