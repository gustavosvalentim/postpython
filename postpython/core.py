import difflib
import json
import re
from copy import copy

import requests

from postpython.extractors import extract_headers, extract_body_data, extract_envvars_from_functions, format_object
from postpython.enqueue import PostRequestQueue


class CaseInsensitiveDict(dict):

    """Dict like object that change all keys to uppercase using key.upper(). """

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(key.upper(), value)

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(key.upper())

    def update(self, d=None, **kwargs):
        d = d or {}
        for k, v in d.items():
            self[k.upper()] = v


class PostPython:
    
    """
    PostPython object storing the postman collection and some metadata from the collection JSON file.
    
    Parameters
    ----------
    postman_collection_json : str
        Postman collection JSON in string format.

    Attributes
    ----------
    __postman_collection_dict : dict
        dict like object got from the Postman Collection JSON file.
    __collection : object
        PostCollection instance.
    __collection_name : str
        Postman collection name
    __collection_schame : str
        Postman collection schema
    __collection_version : int
        Postman collection version
    environments : dict
        CaseInsensitiveDict instance containing environment variables used to assign variant values for the requests.
    """

    __postman_collection_dict = dict()
    __collection = None
    __collection_name = str()
    __collection_schema = str()
    __collection_version = int()
    environments = dict()
    
    def __init__(self, postman_collection_json):
        self.__postman_collection_dict = json.loads(postman_collection_json)
        self.__collection_name = self.__postman_collection_dict['info']['name']
        self.__collection_schema = self.__postman_collection_dict['info']['schema']
        self.__collection_version = self.__get_collection_version()
        self.__collection = None
        self.environments = CaseInsensitiveDict()

        self.__load()

    def __getattr__(self, item):
        if hasattr(self.__collection, item):
            return getattr(self.__collection, item)

    def help(self):
        print("[*] Possible methods are:")
        for req in self.__collection.get_requests():
            print(req.name, end=', ')
        print()
        self.__collection.help()

    def __get_collection_version(self):
        pattern = r'(v\d+\.\d+\.\d+)'
        search = re.search(pattern, self.__collection_schema)

        if search:
            return search.group()[1:]

    def __load(self):
        """Transform the requests in the Postman JSON file in PostRequest instances, it also assign a PostCollection instance to __collection attribute. """
        id_to_request = dict()
        requests_list = dict()
        folders = dict()
        for req in self.__postman_collection_dict['item']:
            if not 'item' in req:
                requests_list[normalize_func_name(req['name'])] = PostRequest(self, req)
            else:
                folder_requests = list()
                for item in req['item']:
                    folder_requests.append(PostRequest(self, item))
                requests_list[normalize_class_name(req['name'])] = PostFolder(req['name'], folder_requests)

        self.__collection = PostCollection(self.__collection_name, requests_list)

    def run_in_queue(self):
        queue_requests = list(filter(lambda x: isinstance(x, PostRequest), self.__collection.get_requests()))
        queue = PostRequestQueue(queue_requests)

        return queue()


class PostCollection:

    """
    Postman collection object storing folders and requests.

    Parameters
    ----------
    name : str
        Name of the collection to be set on the instance
    requests_list : list
        List of the requests. Each request must be an instance of PostRequest.

    Attributes
    ----------
    name : str
        Name of the collection
    __requests : list
        List containing the collection requests
    """

    name = ''
    __requests = {}
    __iter_index = 0

    def __init__(self, name, requests_list):
        self.name = name
        self.__requests = requests_list

    def __getattr__(self, item):
        if item in self.__requests:
            return self.__requests[item]
        if item == 'name':
            return self.name
        else:
            post_requests = list(self.__requests.keys())
            similar_requests = difflib.get_close_matches(item, post_requests, cutoff=0.0)
            if len(similar_requests) > 0:
                similar = similar_requests[0]
                raise AttributeError('%s request does not exist in %s folder.\n'
                                     'Did you mean %s' % (item, self.name, similar))
            else:
                raise AttributeError('%s request does not exist in %s folder.\n'
                                     'Your choices are: %s' % (item, self.name, ", ".join(post_requests)))

    def __len__(self):
        return len(self.__requests)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__iter_index == len(self.__requests):
            raise StopIteration
        else:
            cur_key = list(self.__requests.keys())[self.__iter_index]
            cur_request = self.__requests[cur_key]
            self.__iter_index += 1

            return cur_request

    def help(self):
        for req in self.__requests.keys():
            print("post_python.{REQUEST}()".format(REQUEST=req))

    def get_requests(self):
        return list(map(lambda k, v: v, [*self.__requests.keys()], [*self.__requests.values()]))


class PostRequest:

    """
    Represents a Postman request.

    Parameters
    ----------
    post_python : object
        Current PostPython instance, it will be used to copy the environment, instead of changing it.
    data : dict
        Dict like object containing the request object from a postman collection or folder.

    Attributes
    ----------
    name : str
        Name of the request, it will be transformed to lowercase.
    post_python : object
        Current PostPython instance.
    event : dict
        Dict like object with the events to be runned before and after the request.
    request_kwargs : dict
        Dict like object storing the parameters used to make the request.
    """

    name = str
    post_python = None
    event = dict
    request_kwargs = dict

    def __init__(self, post_python, data):
        self.name = normalize_func_name(data['name'])
        self.post_python = post_python
        self.event = data['event'] if 'event' in data else None
        self.request_kwargs = dict()

        self.request_kwargs['url'] = data['request']['url']['raw']

        if data['request']['body']['mode'] == 'raw' and 'raw' in data['request']['body']:
            self.request_kwargs['json'] = extract_body_data(data['request']['body']['raw'])
            
        self.request_kwargs['headers'] = extract_headers(data['request']['header'])
        self.request_kwargs['method'] = data['request']['method']

    def __call__(self, *args, **kwargs):
        new_env = copy(self.post_python.environments)

        scripts = self.__map_scripts()
        
        if 'prerequest' in scripts:
            new_env.update(scripts['prerequest'])

        new_env.update(kwargs)
        formatted_kwargs = format_object(self.request_kwargs, new_env)
        response = requests.request(**formatted_kwargs)

        if 'test' in scripts:
            self.post_python.environments.update(self.__map_scripts(response)['test'])

        return response

    def __map_scripts(self, response = None):

        """If a pre-request script exists in the postman request, it will parse all `pm.environment.set` functions and replace it on the request template with the values. """

        scripts_results = dict()

        if self.event:
            scripts = list(map(
                lambda e: {'type': e['listen'], 'payload': e['script']['exec']}, self.event))

            if len(scripts) > 0:
                for script in scripts:
                    scripts_results[script['type']] = extract_envvars_from_functions(script['payload'], response = response if response else None)
        
        return scripts_results


class PostFolder:
    
    """
    Postman folder, it is used to organize requests.

    Parameters
    ----------
    name : str
        Postman folder name to be identified in the PostCollection object.
    requests_list : list
        A list that contains the requests inside of Postman folder. Each item on the list must be an instance of PostRequest
    
    Attributes
    ----------
    __name : str
        Postman folder name
    __requests : list
        List of PostRequest objects
    """
    
    __name = ""
    """Folder name. """
    __requests = []
    """Requests inside this folder """

    def __init__(self, name, requests_list):
        self.__name = name
        self.__requests = requests_list

    def __getattr__(self, attr):
        if attr == 'name':
            return self.__name

        all_requests = list(map(lambda req: req.name, self.__requests))
        filter_requests = list(filter(lambda req: req.name == attr, self.__requests))
        if len(filter_requests) > 0:
            return filter_requests[0]
        else:
            raise ValueError(f"Attribute not found: {attr}, your choices are: {', '.join(all_requests)}")

    def __call__(self):
        queue = PostRequestQueue(self.__requests)
        return queue()


def normalize_class_name(string):
    string = re.sub(r'[?!@#$%^&*()_\-+=,./\'\\\"|:;{}\[\]]', ' ', string)
    return string.title().replace(' ', '')


def normalize_func_name(string):
    string = re.sub(r'[?!@#$%^&*()_\-+=,./\'\\\"|:;{}\[\]]', ' ', string)
    return '_'.join(string.lower().split())
