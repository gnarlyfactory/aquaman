"""
power.py

Handle the control of power to any devices plugged into the
electric outlets.
"""
import logging
import threading
import datetime

ON = True
OFF = False

def turn_on(device, callback):
    log = logging.getLogger(__name__)
    log.info("Turning on device '%s'" % device)

    if callback is not None:
        callback(ON)

def turn_off(device, callback=None):
    log = logging.getLogger(__name__)
    log.info("Turning off device '%s'" % device)
    
    if callback is not None:
        callback(OFF)

def schedule_on(device, when, callback):
    """
    Schedule the time for a device to be turned on. The variable
    'when' should be a datetime object in UTC time.
    """
    log = logging.getLogger(__name__)
    log.info("Scheduling device '%s' to turn on at %s" % (device, when))
    delay = (when - datetime.datetime.utcnow()).total_seconds()
    callback_proj = lambda *a, **kwargs: callback(when, device, *a, **kwargs)
    timer = threading.Timer(delay, turn_on, (device,), {'callback':callback_proj})
    timer.start()
    return timer

def schedule_off(device, when, callback):
    """
    Schedule the time for a device to be turned off. The variable
    'when' should be a datetime object in UTC time.
    """
    log = logging.getLogger(__name__)
    log.info("Scheduling device '%s' to turn off at %s" % (device, when))
    delay = (when - datetime.datetime.utcnow()).total_seconds()
    callback_proj = lambda *a, **kwargs: callback(when, device, *a, **kwargs)
    timer = threading.Timer(delay, turn_off, (device,), {'callback':callback_proj})
    timer.start()
    return timer


class PowerScheduler:
    """
    PowerScheduler is a class which will control the power of a single device
    given a schedule of times of day to turn off and turn on.
    """

    def __init__(self, device, on_times, off_times):
        """
        Create a PowerScheduler. This will not start the scheduler. To start
        the scheduler, call the start() function of the instance.
        'device' is the device that this scheduler will control.
        'on_times' is the list of UTC times that the power should be turned on.
        'off_times' is the lest of UTC times that the power should be turned off.
        """
        self.device = device
        self.on_times = on_times
        self.off_times = off_times

        # the currently pending timer
        self._timer = None

        # information about the current state
        self.current_time = None
        self.current_state = None

        # information about the next state
        self.next_time = None
        self.next_state = None

    def start(self):
        """
        Start the PowerScheduler
        """
        log = logging.getLogger(__name__)
        log.info("Starting scheduler for device '%s'" % self.device)
        time, state = self._next()
        self._timer = self._schedule(time, state)

    def stop(self):
        """
        Stop the PowerScheduler and cancel the next state change
        """
        self._timer.cancel()
        log = logging.getLogger(__name__)
        log.info("Stopped scheduler for device '%s'" % self.device)


    def _schedule(self, time, state):
        """
        Schedule a timer to enable a state at a particular time
        """
        timer = None

        if state == ON:
            timer = schedule_on(self.device, time, self._event)
        elif state == OFF:
            timer = schedule_off(self.device, time, self._event)
        else:
            log = logging.getLogger(__name__)
            log.warn("Unknown state: %s" % state)

        return timer

    def _event(self, when, device, state):
        """
        The callback function when a state is changed.
        'when' is the scheduled time of the state change
        'state' is the state that has been set
        'device' is the device that the state was changed on
        """
        self.current_state = state
        self.current_time = when

        time, state = self._next(when)
        self.next_time = time
        self.next_state = state

        self._timer = self._schedule(time, state)

    def _next(self, mark=None):
        """
        Get the next time and state to change to.
        """
        if mark is None:
            mark = self.current_time

        times = [(x, ON) for x in self.on_times] + [(x, OFF) for x in self.off_times]
        times = sorted(times, key=lambda x:x[0])
        next = None
        now = datetime.datetime.utcnow()

        for time, state in times:
            if mark is None:
                if time <= now.time():
                    next = (time, state)
            else:
                if time > mark.time():
                    next = (time, state)

        if mark is None:
            if next is None:
                next = times[len(times - 1)]
                yesterday = now.date() - datetime.timedelta(days=1)
                next = (datetime.datetime.combine(yesterday, next[0]), next[1])
            else:
                next = (datetime.datetime.combine(now.date(), next[0]), next[1])
        else:
            if next is None:
                next = times[0]
                tomorrow = self.current_time.date() + datetime.timedelta(days=1)
                next = (datetime.datetime.combine(tomorrow, next[0]), next[1])
            else:
                next = (datetime.datetime.combine(self.current_time.date(), next[0]), next[1]) 
        
        return next

        
        
