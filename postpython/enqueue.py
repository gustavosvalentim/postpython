class PostRequestQueue:
    
    """
    Create a queue to run the collection requests.
    
    Parameters
    ----------
    requests : list
        List of initial requests to be made in this queue.

    Attributes
    ----------
    __requests : list
        List of requests objects. Each request object must be an instance of PostRequest.
    """

    __requests = list()
    """List of requests. """

    def __init__(self, requests):
        cur_index = len(requests)
        while cur_index > 0:
            self.__requests.append(requests[cur_index - 1])
            cur_index -= 1

    def __call__(self):
        for i in range(len(self.__requests)):
            response = self.__requests[i]()
            if i == len(self.__requests) - 1:
                return response.json()