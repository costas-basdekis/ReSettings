from utils import class_public_dict


class DereferenceContext(object):
    """
    Used to track cyclic dependencies, and keeping a cache for computed items
    """
    def __init__(self, source, cache=None, chain_set=None, chain=None):
        self.source = source
        self.cache = cache or {}
        self.chain_set = chain_set or set()
        self.chain = chain or tuple()

    def extend(self, item):
        if item in self.chain_set:
                raise Exception('Recrusion while evaluating %s: %s' % (item,
                    ' -> '.join(repr(item) for item in self.chain)
                ))

        chain_set = self.chain_set | {item}
        chain = self.chain + (item,)
        return DereferenceContext(self.source, self.cache, chain_set, chain)


class SettingReference(object):
    """
    A basic observable, that can be combined with other for simple expression
    capturing
    """
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
    """
    The value of a setting
    """
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


class SRComputed(SettingReference):
    """
    Dynamically compute a setting by using a callback in the form of:
    lambda SR: ...
    where `SR.setting` returns the calculated `setting` value
    """
    def __init__(self, callback):
        super(SRComputed, self).__init__()
        self.callback = callback

    def dereference_full(self, context):
        derefrencer = Dereferncer(context)
        value = self.callback(derefrencer)
        return value


class SettingReferenceFactory(dict):
    """
    Sortcut for creating combinamble refernces
    """
    def __getattribute__(self, name):
        """
        Dot notation: SR.setting
        """
        if name not in self:
            self[name] = SRPrimitive(name)
        return self[name]

    def __call__(self, callback):
        """
        Call notation: SR(lambda SR:...)
        """
        if callback not in self:
            self[callback] = SRComputed(callback)
        return self[callback]
setting_reference_factory = SettingReferenceFactory()


class Dereferncer(object):
    """
    Proxy object for use inside lambdas in computed
    """
    def __init__(self, context):
        self.context = context

    def __getattribute__(self, name):
        context = super(Dereferncer, self).__getattribute__('context')
        reference = getattr(setting_reference_factory, name)
        value = dereference_item(reference, context)
        return value


def dereference_item(item, context):
    """
    Sortcut for getting the real value of an item
    """
    if not isinstance(item, SettingReference):
        return item

    return item.dereference(context)


def dereference_dict(source):
    """
    Sortcut for getting the real values inside a dict
    """
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