# -*- coding=utf-8 -*-


class HashableDict(dict):
    def __init__(self, *args, **kwargs):
        super(HashableDict, self).__init__(*args, **kwargs)

        for k, v in self.items():
            if type(v) is dict:
                self[k] = HashableDict(v)
            elif type(v) is list:
                self[k] = HashableList(v)

    def __hash__(self):
        return hash(tuple(sorted(self.items())))


class HashableList(list):
    def __hash__(self):
        return hash(tuple(self))


