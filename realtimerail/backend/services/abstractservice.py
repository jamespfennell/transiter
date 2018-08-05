



class AbstractService():
    def __init__(self):
        # Assign manager in child clases

    @jsonifyoutput
    def get_by_id(id):
        try:
            response = manager.get_by_id()
        except InvalidId:
            flask(404)
        return response

    @jsonifyoutput
    def list():
        manager.list()


Handles outputting to JSON, for example

Or catching validation errors - automaically throws 404
