import pytz
import datetime

def convert_to_utc(dt, tz):
    """
    Convert datetime instance dt localized to tz into a utc datetime.
    """
    local = pytz.timezone(tz)
    localdt = local.localize(dt)
    localdt = pytz.utc.normalize(localdt)
    utcdt = localdt.astimezone(pytz.utc)
    return utcdt

def convert_to_local(dt, tz):
    """
    Convert a utc datetime instance dt to a utc datetime
    """
    local = pytz.timezone(tz)

    if dt.tzinfo is None:
        utcdt = pytz.utc.localize(dt)
    else:
        utcdt = dt.replace(tzinfo=pytz.utc)

    utcdt = local.normalize(utcdt)
    localdt = utcdt.astimezone(local)
    return localdt


if __name__ == '__main__':
    # test the timezone conversions
    zone = "America/New_York"
    localdt = datetime.datetime.now()
    utcdt = datetime.datetime.utcnow()

    utcdt2 = convert_to_utc(localdt, zone)
    local2 = convert_to_local(utcdt2, zone)
    local3 = convert_to_local(utcdt, zone)

    fmt = "%Y-%m-%d %H:%M:%S %Z%z"
    print "Local:             {}".format(localdt.strftime(fmt))
    print "Local->UTC:        {}".format(utcdt2.strftime(fmt))
    print "Local->UTC->Local: {}".format(local2.strftime(fmt))
    print "UTC->Local:        {}".format(local3.strftime(fmt))
