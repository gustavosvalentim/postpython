from postpython.core import PostPython

pp = None

with open('PATH_TO_YOUR_POSTMAN_COLLECTION', encoding="utf-8") as fhandler:
    pp = PostPython(fhandler.read())

pp.environments.update({"ENVVAR": "ABC"})
response = pp.testrequest()
print(response.json())
