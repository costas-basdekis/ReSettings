def public_dict(d):
    return {
        key: value
        for key, value in d.iteritems()
        if not (key.startswith('__') and key.endswith('__'))
    }


def class_public_dict(cls):
    try:
        bases = cls.__bases__
    except AttributeError:
        bases = []

    d = {}
    for base in reversed((cls,) + bases):
        d.update(public_dict(base.__dict__))

    return d
