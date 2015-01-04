class FilterModule(object):
    def filters(self):
        return [multiget]


def multiget(dictionary, keys):
    return [dictionary[k] for k in keys]
