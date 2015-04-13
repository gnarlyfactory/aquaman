import power
import datetime
import logging
import pytz

def done(when, device, powerstate):
    log = logging.getLogger(__name__)
    log.info("Power to device '%s' has been set to %s" % (device, powerstate))

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.ini')
    log = logging.getLogger(__name__)

    schedules = power.load_schedule('config/power.txt')

    for device, schedule in schedules.items():
        s = power.PowerScheduler(device, schedule.on_times, schedule.off_times)
        s.start()
