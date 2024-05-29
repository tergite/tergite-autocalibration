class ClusterNotFoundError(BaseException):
    def __init__(self, msg: str):
        self.__msg = msg

    def __repr__(self):
        return f'ClusterNotFoundError: {self.__msg}'

    def __str__(self):
        return self.__msg
