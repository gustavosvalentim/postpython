import json, re


POSTMAN_FUNCTIONS_MAPPING = {
    'pm.environment.set': {
        'regex_pattern': r'pm\.environment\.set\(.*\)',
    }
}

POSTMAN_VARS_MAPPING =  {
    'jsonData': {
        'regex_pattern': r'jsonData\.(\w+|\_)',
        'sub': r'jsonData\.'
    }
}


def extract_body_data(raw):

    """
    Extract ``JSON`` data from the request body and transform in a dict like object.
    
    ``raw`` is a ``json string`` required, it will be transformed in a ``dict``, in case of errors to decode the ``json``, will be raised a ``JSONDecodeError`` exception.
    """

    try:
        return json.loads(raw)
    except json.decoder.JSONDecodeError:
        return {}


def extract_headers(input_headers):
    d = {}
    for header in input_headers:
        d[header['key']] = header['value']

    return d


def extract_postman_functions(pattern, line):
    results = {}
    regex_match = re.search(pattern, line)

    if regex_match:
        regex_result = regex_match.group()
        parameters_pattern = r'\(.+\,.+\)'
        parameters_re = re.search(parameters_pattern, regex_result)
        
        if parameters_re:
            parameters = parameters_re.group()

            if parameters.startswith('('):
                parameters = parameters[1:len(parameters) - 1]
                parameters = [param.rstrip().lstrip() for param in parameters.split(',')]

                key, value = list(map(lambda x: x[1:len(x) - 1] if x.startswith('"') else x, parameters))
            
            results[key] = value

    return results


def extract_postman_variable(patterns, response_var_name, response):
    results = {}
    regex_match = re.search(patterns['regex_pattern'], response_var_name)

    if regex_match:
        envvar_value = regex_match.group()
        envvar_value = re.sub(patterns['sub'], '', envvar_value)

        if envvar_value:
            return response.json()[envvar_value]
            
def extract_envvars_from_functions(pre_request, response = None):
    results = dict()

    for line in pre_request:
        for k, v in POSTMAN_FUNCTIONS_MAPPING.items():
            pattern = v['regex_pattern']
            envvars_from_functions = extract_postman_functions(pattern, line)

            results.update(envvars_from_functions)

    if response:
        for envvar_key, envvar_value in results.items():
            for k, v in POSTMAN_VARS_MAPPING.items():
                results[envvar_key] = extract_postman_variable(v, envvar_value, response)

    return results


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
