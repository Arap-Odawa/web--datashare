import sys
import datetime
from loguru import logger
import functools
#from loguru import logger

class Rotator:
    def __init__(self, *, size, at):
        now = datetime.datetime.now()

        self._size_limit = size
        self._time_limit = now.replace(hour=at.hour, minute=at.minute, second=at.second)

        if now >= self._time_limit:
            # The current time is already past the target time so it would rotate already.
            # Add one day to prevent an immediate rotation.
            self._time_limit += datetime.timedelta(days=1)

    def should_rotate(self, message, file):
        file.seek(0, 2)
        if file.tell() + len(message) > self._size_limit:
            return True
        excess = message.record["time"].timestamp() - self._time_limit.timestamp()
        if excess >= 0:
            elapsed_days = datetime.timedelta(seconds=excess).days
            self._time_limit += datetime.timedelta(days=elapsed_days + 1)
            return True
        return False

# The above rotator function is setup to have the rotation to accept either file-size based (500MB) rotation
# or time based rotation ie every midnight     

rotator = Rotator(size=5e+8, at=datetime.time(0, 0, 0))

#logger.add("app.log", 
#           rotation=rotator.should_rotate, 
#           level="INFO", 
#           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra[ip]} | {extra}",
#           compression="zip",
#        
#           enqueue=True,
#           )



def logger_wraps(*, entry=True, exit=True, level="INFO"):

    def wrapper(func):
        name = func.__name__

        @functools.wraps(func)
        def wrapped(user_ext_uuid='check_user', user_ip_address='0.0.0.0.', *args, **kwargs):
            logger_ = logger.opt(depth=1)
            if entry:
                logger_.log(level, "User '{}' running on IP address '{}' is Entering '{}' (args={}, kwargs={})",user_ext_uuid, user_ip_address, name, args, kwargs)
            result = func(*args, **kwargs)
            if exit:
                logger_.log(level, "User '{}' running on IP address '{}' is Exiting '{}' (result={})",user_ext_uuid, user_ip_address, name, result)
            return result

        return wrapped

    return wrapper