
class readUrl:
    def __init__(self, url, param):
        self.url = url
        self.param = param

    def greet(self):
        return f"Hitting {self.url} with param {self.param}"
