from utils import class_public_dict

class SettingReference(object):
    def __init__(self, name):
        self.name = name

    def dereference(self, context):
        value = self

        chain_set, chain = set(), []
        while isinstance(value, SettingReference):
            if value in chain_set:
                raise Exception("Circular dependency detected: %s" % ' -> '.join(
                    item.name for item in chain
                ))
            chain_set.add(value)
            chain.append(value)
            value = context[value.name]

        return value


class SettingReferenceFactory(dict):
    def __getattribute__(self, name):
        if name not in self:
            self[name] = SettingReference(name)
        return self[name]
setting_reference_factory = SettingReferenceFactory()

def dereference(context):
    for key, value in context.iteritems():
        if isinstance(value, SettingReference):
            context[key] = value.dereference(context)


class SettingsBag(object):
    @classmethod
    def as_dict(cls):
        context = class_public_dict(cls)

        dereference(context)

        return context