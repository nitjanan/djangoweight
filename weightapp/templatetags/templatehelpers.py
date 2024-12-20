from django import template
from datetime import timedelta

register = template.Library()

@register.simple_tag
def my_url(value, field_name, urlencode=None):
    url = '?{}={}'.format(field_name, value)
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url

@register.filter
def format_duration(duration):
    result = None
    if duration:
        hours = duration // timedelta(hours=1)
        minutes = (duration % timedelta(hours=1)) // timedelta(minutes=1)
        result = f"{hours:02d}:{minutes:02d}"
    else:
        result = f"{0}:{0:02d}"
    return result

@register.filter
def format_duration_substring(tmpStr):
    return str(tmpStr)[:-3]

@register.filter
def dict_keys(input_dict):
    return input_dict.keys()