class UserNotFoundException(Exception):
    pass


class ParametrNotFoundException(Exception):
    pass

class ModelProblems(Exception):
    val = ""
    def __init__(self, text):
        self.val = self.val + text
        self.txt = self.val


