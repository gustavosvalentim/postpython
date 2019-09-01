# Postpython
Postpython is a library for [Postman](https://www.getpostman.com/) that run Postman's collections.
If you are using postman, but collection runner is not flexible enough for you and postman codegen is too boring,
Postpython is here for your continuous integration.

## Why use Postpython instead of postman codegen?
- Postman codegen should be applied one by one for each request and it's boring when your API changes,
 but with postpython, you don't need to generate code.
 Just export collection with Postman and use it with Postpython.
- Postpython interprets `pm.environment.set()` function, so you can set your environment fine.
- Postpython will interpret `jsonResponse` variable as the request response in JSON format.
- Postpython have the ability to run your collection requests in a queue, returning only the response from the last request.

## Why user Postpython instead of Postman collection runner?
- With postpython, you write your own script. But collection runner just turns all your requests one by one.
So with Postpython, you can design more complex test suites.

## How to install?
Postpython is available on [Git](https://github.com/gustavosvalentim/postpython)

## How to use?

Import `PostPython`
```$python
from postpython.core import PostPython
```
Make an instance from `PostPython` and give the address of postman collection file.
```$python
runner = PostPython(YOUR_POSTMAN_COLLECTION_JSON_AS_STRING)
```
Now you can call your request. Folders' name change to upper camel case and requests' name change to lowercase form.
In this example the name of folder is "Request Methods" and it's change to `RequestMethods` and the name of request was
"GET Request" and it's change to `get_request`. So you should call a function like `runner.YourFolderName.you_request_name()`
```$python
response = runner.RequestMethods.get_request()
print(response.json())
print(response.status_code)
```

You can run your requests in a queue.
```$python
response = runner.FolderName.run_in_queue()
```

### Variable assignment
In Postpython you can assign values to environment variables in runtime.
```
runner.environments.update({'BASE_URL': 'http://127.0.0.1:5000'})
runner.environments.update({'PASSWORD': 'test', 'EMAIL': 'you@email.com'})
```
### AttributeError
Since `RequestMethods` and `get_request` does not really exists your intelligent IDE cannot help you.
So Postpython tries to correct your mistakes. If you spell a function or folder wrong it will suggest you the closest name.
```
>>> response = runner.RequestMethods.get_requasts()

Traceback (most recent call last):
  File "test.py", line 11, in <module>
    response = runner.RequestMethods.get_requasts()
  File "/usr/local/lib/python3.5/site-packages/postpython/core.py", line 73, in __getattr__
    'Did you mean %s' % (item, self.name, similar))
AttributeError: get_requasts request does not exist in RequestMethods folder.
Did you mean get_request

```
You can also use `help()` method to print all available requests.
```
>>> runner.help()
Posible requests:
runner.AuthOthers.hawk_auth()
runner.AuthOthers.basic_auth()
runner.AuthOthers.oauth1_0_verify_signature()
runner.RequestMethods.get_request()
runner.RequestMethods.put_request()
runner.RequestMethods.delete_request()
runner.RequestMethods.post_request()
runner.RequestMethods.patch_request()
...

>>> runner.RequestMethods.help()
runner.RequestMethods.delete_request()
runner.RequestMethods.patch_request()
runner.RequestMethods.get_request()
runner.RequestMethods.put_request()
runner.RequestMethods.post_request()

```

## Contribution
Feel free to share your ideas or any problems in [issues](https://github.com/gustavosvalentim/postpython/issues).
Contributions are welcomed. Give postpython a star to encourage me to continue its development.

**This project was forked from [k3rn3l-p4n1c/postpython](https://github.com/k3rn3l-p4n1c/postpython)**
