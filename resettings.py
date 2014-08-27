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


def operator(name):
    """
    Operator factory
    """
    def __op__(*args):
        return SROperator(name, args)
    __op__.name = name

    return __op__
unary_operators = ['__not__', 'truth', '__abs__', '__index__', '__invert__',
    '__neg__', '__pos__',
]
binary_operators = ['__lt__', '__le__', '__eq__', '__ne__', '__ge__', '__gt__',
    '__add__', '__and__', '__div__', '__floordiv__', '__lshift__', '__mod__',
    '__mul__', '__sub__', '__or__', '__pow__', '__rshift__', '__sub__',
    '__turediv__', '__xor__', '__concat__', '__contains__', 'is_', 'is_not'
]
for op in unary_operators + binary_operators:
    setattr(SettingReference, op, operator(op))


def r_binary_operator(name):
    """
    Reversed binary operator factory
    """
    r_name = name.replace('__r', '__')
    def __rbinop__(self, other):
        return SROperator(r_name, (other, self))
    __rbinop__.name = name

    return __rbinop__
r_binary_operators = ['__radd__', '__rand__', '__rdiv__', '__rfloordiv__',
    '__rlshift__', '__rmod__', '__rmul__', '__rsub__', '__rpow__', '__rrshift__',
    '__rsub__', '__rtruediv__', '__rxor__', '__rconcat__'
]
for r_op in r_binary_operators:
    setattr(SettingReference, r_op, r_binary_operator(r_op))


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


class SROperator(SettingReference):
    """
    A binary or unary operation of two items
    """
    def __init__(self, operation, args):
        self.operation = operation
        self.args = args

    def __repr__(self):
        return '%s(%s)' % (self.operation, ', '.join(map(repr, self.args)))

    def dereference_full(self, context):
        dargs = [dereference_item(arg, context) for arg in self.args]
        value = getattr(dargs[0], self.operation)(*dargs[1:])

        return value


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