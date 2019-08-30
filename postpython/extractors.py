import json


def extract_body_data(raw):
    try:
        return json.loads(raw)
    except json.decoder.JSONDecodeError:
        return {}


def extract_headers(input_headers):
    d = {}
    for header in input_headers:
        d[header['key']] = header['value']

    return d


def format_object(o, key_values):
    if isinstance(o, str):
        try:
            return o.replace('{{', '{').replace('}}', '}').format(**key_values)
        except KeyError as e:
            raise KeyError(
                "Except value %s in PostPython environment variables.\n Environment variables are %s" % (e, key_values))
    elif isinstance(o, dict):
        return format_dict(o, key_values)
    elif isinstance(o, list):
        return [format_object(oo, key_values) for oo in o]


def format_dict(d, key_values):
    kwargs = {}
    for k, v in d.items():
        kwargs[k] = format_object(v, key_values)
    return kwargs
