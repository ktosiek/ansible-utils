class FilterModule(object):
    def filters(self):
        return [multiget]


def multiget(*args, **kwargs):
    return list(multiget_(*args, **kwargs))


def multiget_(dictionary, keys, ignore_missing=False):
    for k in keys:
        try:
            yield dictionary[k]
        except KeyError:
            if ignore_missing:
                continue
            else:
                raise
