
class Symbol(object):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

class BuiltinFunction(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

class ArraySymbol(Symbol):
    def __init__(self,name,type, from_ , to_):
        super().__init__(name,type)
        self.from_ = from_
        self.to_ = to_
    def __str__(self):
        return '<{name}:{type}[{from_} .. {to_}]>'.format(name = self.name, type = self.type, from_ = self.from_, to_ = self.to_)

class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return '<{name}:{type}>'.format(name=self.name, type=self.type)


class BlockSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return '{name}'.format(name=self.name)


class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None):
        super(ProcedureSymbol, self).__init__(name)
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
    def __init__(self, name, params=None):
        super(FunctionSymbol, self).__init__(name)
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