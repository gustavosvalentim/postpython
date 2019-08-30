from postpython.core import PostPython

pp = None

with open('/home/gustavo/Desktop/TestCollection.postman_collection.json', encoding="utf-8") as fhandler:
    pp = PostPython(fhandler.read())

print(pp.testrequest)
