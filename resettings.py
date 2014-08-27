from utils import class_public_dict


class DereferenceContext(object):
    def __init__(self, source, cache=None, chain_set=None, chain=None):
        self.source = source
        self.cache = cache or {}
        self.chain_set = chain_set or set()
        self.chain = chain or tuple()

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return repr(self)

    def extend(self, item):
        if item in self.chain_set:
                raise Exception('Recrusion while evaluating %s: %s' % (item,
                    ' -> '.join(repr(item) for item in self.chain)
                ))

        chain_set = self.chain_set | {item}
        chain = self.chain + (item,)
        return DereferenceContext(self.source, self.cache, chain_set, chain)


class SettingReference(object):
    def __init__(self):
        self.__cached__ = False
        self.__value__ = None
        self.__chain_set__ = None
        self.__chain__ = None

    def dereference(self, context):
        context = context.extend(self)

        if self not in context.cache:
            value = self.dereference_full(context)
            context.value = value
            context.cache[self] = context
        else:
            value = context.cache[self].value

        return value

    def __add__(left, right):
        return SRPlus(left, right)

    def __radd__(right, left):
        return SRPlus(left, right)

    def __sub__(left, right):
        return SRSub(left, right)

    def __rsub__(right, left):
        return SRSub(left, right)


class SRPrimitive(SettingReference):
    def __init__(self, name):
        super(SRPrimitive, self).__init__()
        self.name = name

    def __repr__(self):
        return '<%s>' % self.name

    def dereference_full(self, context):
        value = dereference_item(context.source[self.name], context)

        return value


class SRPlus(SettingReference):
    def __init__(self, left, right):
        super(SRPlus, self).__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return '%s + %s' % (self.left, self.right)

    def dereference_full(self, context):
        left = dereference_item(self.left, context)
        right = dereference_item(self.right, context)

        return left + right


class SRSub(SettingReference):
    def __init__(self, left, right):
        super(SRSub, self).__init__()
        self.left = left
        self.right = right

    def dereference_full(self, context):
        left = dereference_item(self.left, context)
        right = dereference_item(self.right, context)

        return left - right


class SettingReferenceFactory(dict):
    def __getattribute__(self, name):
        if name not in self:
            self[name] = SRPrimitive(name)
        return self[name]
setting_reference_factory = SettingReferenceFactory()


def dereference_item(item, context):
    if not isinstance(item, SettingReference):
        return item

    return item.dereference(context)


def dereference_dict(source):
    context = DereferenceContext(source)
    return {
        key: dereference_item(value, context)
        for key, value in source.iteritems()
    }


class SettingsBag(object):
    @classmethod
    def as_dict(cls):
        source = class_public_dict(cls)

        d = dereference_dict(source)

        return d