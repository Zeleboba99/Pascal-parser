
class Symbol(object):
    def __init__(self, name, index=None, type=None):
        self.name = name
        self.type = type
        self.index = index


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name, index=None):
        super().__init__(name, index=index)

    def __str__(self):
        return self.name


class BuiltinFunction(Symbol):
    def __init__(self, name, index=None):
        super().__init__(name, index=index)

    def __str__(self):
        return self.name


class VarSymbol(Symbol):
    def __init__(self, name, type, is_field=False, index=None):
        super().__init__(name, index=index, type=type)
        self.is_field = is_field

    def __str__(self):
        return '<{name}:{type}> index:{index} '.format(name=self.name, type=self.type, index=self.index)


class ArraySymbol(VarSymbol):
    def __init__(self, name, type, from_, to_, index=None):
        super().__init__(name, index=index, type=type)
        self.from_ = from_
        self.to_ = to_
    def __str__(self):
        return '<{name}:{type}[{from_} .. {to_}]>'.format(name=self.name, type=self.type, from_=self.from_, to_=self.to_)


class BlockSymbol(Symbol):
    def __init__(self, name, index=None):
        super().__init__(name, index=index)

    def __str__(self):
        return '{name}'.format(name=self.name)


class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None, index=None):
        super(ProcedureSymbol, self).__init__(name, index=index)
        self.params = params if params is not None else []
        #type is None, procedure returns nothing

    def __str__(self):
        def formatter(p):
            return '{name}: {type}'.format(name=str(p.name), type=str(p.type))
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=list(map(formatter, self.params)),
        )


class FunctionSymbol(Symbol):
    def __init__(self, name, params=None, index=None):
        super(FunctionSymbol, self).__init__(name, index=index)
        self.params = params if params is not None else []
        #type is None, procedure returns nothing

    def __str__(self):
        def formatter(p):
            return '{name}: {type}'.format(name=str(p.name), type=str(p.type))
        return '<{class_name}(name={name}, parameters={params}): {type}>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=list(map(formatter, self.params)),
            type=self.type,
        )