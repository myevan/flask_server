from enum import Enum

class classproperty(object):
    def __init__(self, method):
        self.method = method
        self.value = None

    def __get__(self, instance, cls):
        if self.value is None:
            self.value = self.method(cls)
        return self.value
