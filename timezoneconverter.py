from datetime import datetime
from pytz import timezone

#date_str = "2020-03-28 00:47:49 UTC"

def convert(date_str):

    datetime_obj_naive = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %Z")
    datetime_obj_pacific = timezone('UTC').localize(datetime_obj_naive)

    event_time_prague = datetime_obj_pacific.astimezone(timezone('Europe/Prague'))

    return event_time_prague.strftime("%Y-%m-%d %H:%M:%S %Z")

#print(convert(date_str))