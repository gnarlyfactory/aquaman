import power
import datetime
import logging
import pytz
import ConfigParser

def done(when, device, powerstate):
    log = logging.getLogger(__name__)
    log.info("Power to device '%s' has been set to %s" % (device, powerstate))

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('config/logging.ini')
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    config_file = 'config/aquaman.ini'
    log.debug("Loading config file: {}".format(config_file))
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    timezone = config.get('settings', 'timezone')
    log.debug("Time Zone = {}".format(timezone))

    schedules = power.load_schedule('config/power.txt')
    schedulers = []

    for device, schedule in schedules.items():
        s = power.ThreadPowerScheduler(device, schedule.on_times, schedule.off_times)
        schedulers.append(s)
        s.start()
