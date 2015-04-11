import power
import datetime
import logging



def done(when, device, powerstate):
    log = logging.getLogger(__name__)
    log.info("Power to device '%s' has been set to %s" % (device, powerstate))

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.ini')
    log = logging.getLogger(__name__)
    #now = datetime.datetime.utcnow()
    #then = now + datetime.timedelta(seconds=2)
    #power.schedule_off(1, then, callback=done)

    on = [datetime.time(hour=12, minute=0)]
    off = [datetime.time(hour=15, minute=0)]
    s = power.PowerScheduler(1,on, off)
    s.start()
