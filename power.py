"""
power.py

Handle the control of power to any devices plugged into the
electric outlets.
"""
import logging
import threading
import datetime
import csv
import util
import time

# States that power can be
ON = True
OFF = False

# Local time zone for display
ZONE = "America/New_York"

def localize(dt, zone=None):
    """
    Convert a datetime dt to the local timezone.
    zone is an optional timezone. The global ZONE variable will
    be used by default.
    """
    if zone is None:
        return util.convert_to_local(dt, ZONE)
    else:
        return util.convert_to_local(dt, zone)

def turn_on(device, callback=None):
    """
    Turn on a device and call the callback function when the power
    has been turned on.
    """
    log = logging.getLogger(__name__)
    log.info("Turning on device '{}'".format(device))

    if callback is not None:
        callback(ON)

def turn_off(device, callback=None):
    """
    Turn off a device and call the callback function when the power
    has been turned off.
    """
    log = logging.getLogger(__name__)
    log.info("Turning off device '{}'".format(device))
    
    if callback is not None:
        callback(OFF)

def load_schedule(filename):
    """
    Load a schedule from a tab-delimited text file. A dictionary
    of PowerScheulde instances will be returned where the key is
    the device that the PowerSchedule applies to.
    
    The contents of the file at 'filename' should look like this:

    device     time      state
    one        11:00     ON
    one        19:00     OFF
    two        00:00     ON
    two        05:00     OFF
    air        19:00     ON
    air        20:00     OFF

    The device column can be any string, time is a local time HH:MM,
    and state should be either 'ON' or 'OFF'
    """

    schedules = {}
    date = datetime.datetime.now().date()

    with open(filename, 'r') as schedfile:
        reader = csv.reader(schedfile, delimiter="\t")
        n = 0

        for row in reader:
            if n > 0:
                device, time, state = row

                timeobj = datetime.datetime.strptime(time, "%H:%M").time()
                localdt = datetime.datetime.combine(date, timeobj)
                utcdt = util.convert_to_utc(localdt, ZONE)
                timeutc = utcdt.time()

                if device not in schedules:
                    schedules[device] = PowerSchedule(device)

                if state == 'ON':
                    schedules[device].on_times.append(timeutc)
                elif state == 'OFF':
                    schedules[device].off_times.append(timeutc)
            n += 1

    return schedules


class PowerSchedulerState:
    """
    PowerScheulerState represents a state that a device controlled
    by a PowerScheulder should be set to at a specific time.
    """

    def __init__(self, time, state):
        """
        Create an instance of PowerSchedulerState using a UTC time and a state.
        time is the UTC time that the state should be as of
        state is the state that the associated device should be in as of time
        """
        self.time = time
        self.state = state


class PowerScheduler(threading.Thread):
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
        threading.Thread.__init__(self)
        self.device = device
        self.states = [PowerSchedulerState(x, ON) for x in on_times]
        self.states += [PowerSchedulerState(x, OFF) for x in off_times]
        self.states = sorted(self.states, key=lambda x:x.time)
        self._stopped = False


    def __initial_state(self):
        """
        Get the initial state that the device should be at the current
        time, based on the schedule of states for this device
        """

        now = datetime.datetime.utcnow()
        yesterday = now.date() - datetime.timedelta(days=1)
        state = None

        # find the initial state, the last state before the current time
        for s in self.states:
            if s.time <= now.time():
                state = s

        # if no state was found before the current time, the current 
        # state is the last state from the prior day
        if state is None:
            state = self.states[len(self.states) - 1]

        return state


    def __set_state(self, state):
        """
        Set the state (turn on or off) of the device for this scheduler.
        """

        if state.state == ON:
            turn_on(self.device)
        elif state.state == OFF:
            turn_off(self.device)


    def run(self):
        """
        Run the scheduler, looping until stop() is called
        """

        log = logging.getLogger(__name__)
        self._stopped = False
        state = self.__initial_state()

        try:
             while not self._stopped:
                self.__set_state(state)
                now = datetime.datetime.utcnow()
                next_state = None

                # find the next state
                for s in self.states:
                    if s.time > state.time:
                        next_state = s
                        break

                # next is the datetime to switch to next_state
                next = None
                if next_state is None:
                    next_state = self.states[0]
                    tomorrow = now.date() + datetime.timedelta(days=1)
                    next = datetime.datetime.combine(tomorrow, next_state.time)
                else:
                    next = datetime.datetime.combine(now.date(), next_state.time)

                state = next_state
                
                # sleep until the next state's time
                delay = (next - now).total_seconds()
                
                if delay >= 0:
                    log.debug("Device '{}' is waiting until {} to turn {}".format(self.device, localize(next), state.state))
                    time.sleep(delay)
                
        except KeyboardInterrupt:
            pass

    def start(self):
        """
        Start the scheduler
        """

        log = logging.getLogger(__name__)
        log.info("Starting scheduler for device '{}'".format(self.device))
        threading.Thread.start(self)


    def stop(self):
        """
        Stop the PowerScheduler and cancel the next state change
        """
        log = logging.getLogger(__name__)
        log.info("Stopped scheduler for device '{}'".format(self.device))
        self.__stopped = True


class PowerSchedule:
    """
    PowerSchedule contains the information of the schecdule of power on
    and off times.
    """

    def __init__(self, device):
        """
        Create a new PowerSchedule
        """
        self.device = device
        self.on_times = []
        self.off_times = []

