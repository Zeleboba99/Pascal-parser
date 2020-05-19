from nodes import *
from grammar import *
from symbols import *


class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level, enclosing_scope=None):
        self._symbols = {}
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self.init_builtins()

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
                ('Scope name', self.scope_name),
                ('Scope level', self.scope_level),
                ('Enclosing scope',
                 self.enclosing_scope.scope_name if self.enclosing_scope else None
                )
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, str(value)))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    def init_builtins(self):
        self.define(BuiltinTypeSymbol('integer'))
        self.define(BuiltinTypeSymbol('char'))
        self.define(BuiltinTypeSymbol('boolean'))

    def define(self, symbol: Symbol):
        print('Define: %s' % symbol)
        self._symbols[symbol.name] = symbol

    def lookup(self, name, current_scope_only=False) -> Symbol:
        print('Lookup: %s' % name)
        symbol = self._symbols.get(name)
        if symbol is not None:
            return symbol

        if current_scope_only:
            return None

        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)



class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        # self.global_scope = ScopedSymbolTable(scope_name='global', scope_level=1)
        # self.current_scope = self.global_scope
        self.dictionary = {'int':'integer', 'str':'char','bool':'boolean'}
        self.current_scope = None

    def __typeChecker(self, type1, type2):
        if(type1 is None or type2 is None):
            return True
        for key in self.dictionary:
            if(type1 == key and type2 == self.dictionary[key]):
                return True
        return False

    #попробовать интегрировать проверку ссюда
    def visit_BinOpNode(self, node):
        self.visit(node.arg1)
        self.visit(node.arg2)

    def visit_IdentNode(self, node: IdentNode):
        var_name = node.name
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            raise Exception("Symbol(identifier) not found '%s'" % var_name)
        return var_symbol.type.name

    def visit_LiteralNode(self, node: LiteralNode):
        return type(node.value).__name__

    def visit_ProgramNode(self, node: ProgramNode):
        print('ENTER scope: global')
        self.global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = self.global_scope
        self.visit(node.vars_decl)
        self.visit(node.stmt_list)
        print(self.current_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: global')

    def visit_VarsDeclNode(self, node: VarsDeclNode):
        for var_decl in node.var_decs:
            self.visit(var_decl)

    def visit_VarDeclNode(self, node: VarDeclNode):
        type_symbol = self.current_scope.lookup(node.vars_type.name)
        for ident in node.ident_list.idents:
            var_name = ident.name
            var_symbol = VarSymbol(var_name, type_symbol)
            #only for current scope
            if self.current_scope.lookup(var_name, current_scope_only=True):
                raise Exception(
                    "Duplicate identifier '%s' found" % var_name
                )
            self.current_scope.define(var_symbol)
    def visit_ArrayDeclNode(self, node: ArrayDeclNode):
        type = node.vars_type
        from_ = node.from_.literal
        to_ = node.to_.literal
        for ident in node.name.idents:
            arr_name = ident.name
            arr_symb = ArraySymbol(arr_name,type,from_,to_)
            if self.current_scope.lookup(arr_name,current_scope_only=True):
                raise Exception(
                    "Duplicate identifier '%s' found" % arr_name
                )
            self.current_scope.define(arr_symb)

    def visit_ArrayIdentNode(self, node : ArrayIdentNode):
        arr_name = node.name.name
        liter = int(node.literal.literal)
        arr_symbol : ArraySymbol = self.current_scope.lookup(arr_name)
        if(liter < int(arr_symbol.from_) or liter > int(arr_symbol.to_)):
            raise Exception("Out of range '%s'" % liter)



    def visit_BodyNode(self, node: BodyNode):
        self.visit(node.body)

    def visit_StmtListNode(self, node: StmtListNode):
        for stmt in node.exprs:
            self.visit(stmt)

    #TODO rewrite it
    def visit_AssignNode(self, node: AssignNode):
        var = node.var
        visit = None
        type_val =None

        if( isinstance(var,ArrayIdentNode) ):
            var_name = var.name.name
            visit = var
            type_val = type(node.val.value).__name__
        else:
            var_name = var.name
            visit = node.val
        var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            #raise NameError(var_name)
            raise Exception(
                "Undefined variable '%s' found" % var_name
            )
        type_visited = self.visit(visit)
        if type_val is None: type_val=type_visited
        if not (self.__typeChecker(type_val, var_symbol.type.name) or type_val == var_symbol.type.name):
            raise Exception(
                "Wrong type '%s' found" % var_name
            )

    def visit_ProcedureDeclNode(self, node: ProcedureDeclNode):
        proc_name = node.proc_name
        proc_symbol = ProcedureSymbol(proc_name)
        self.current_scope.define(proc_symbol)

        print('ENTER scope: %s' % proc_name)
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )

        self.current_scope = procedure_scope
        #for param in node.params:
        param_type = self.current_scope.lookup(node.params.vars_type[0].name)
        #for param_name in node.params.vars_list:
        var_symbol = VarSymbol(node.params.vars_list, param_type)
        self.current_scope.define(var_symbol)
        proc_symbol.params.append(var_symbol)

        for stmt in node.stmt_list.body.exprs:
            self.visit(stmt)

        print(procedure_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s' % proc_name)

    def visit_CallNode(self, node: CallNode):
        f=1
        for param in node.params:
            self.visit(param)

    def visit_IfNode(self, node: IfNode):
        self.visit(node.cond)
        # THEN SCOPE
        # then_block_symbol = BlockSymbol('THEN BODY')
        # self.current_scope.define(then_block_symbol)
        #
        # print('ENTER scope: %s' % then_block_symbol)
        # then_block_scope = ScopedSymbolTable(
        #     scope_name=then_block_symbol,
        #     scope_level=self.current_scope.scope_level + 1,
        #     enclosing_scope=self.current_scope
        # )
        # self.current_scope = then_block_scope
        self.visit(node.then_stmt)
        # print(then_block_scope)
        # self.current_scope = self.current_scope.enclosing_scope
        # print('LEAVE scope: %s' % then_block_symbol.name)

        # ELSE SCOPE
        if node.else_stmt:
            # else_block_symbol = BlockSymbol('ELSE BODY')
            # self.current_scope.define(else_block_symbol)
            #
            # print('ENTER scope: %s' % else_block_symbol)
            # else_block_scope = ScopedSymbolTable(
            #     scope_name=else_block_symbol,
            #     scope_level=self.current_scope.scope_level + 1,
            #     enclosing_scope=self.current_scope
            # )
            # self.current_scope = else_block_scope
            self.visit(node.else_stmt)
            # print(else_block_scope)
            # self.current_scope = self.current_scope.enclosing_scope
            # print('LEAVE scope: %s' % else_block_symbol.name)


    def visit_WhileNode(self, node: WhileNode):
        self.visit(node.cond)
        # block_symbol = BlockSymbol('WHILE BODY')
        # self.current_scope.define(block_symbol)
        #
        # print('ENTER scope: %s' % block_symbol)
        # block_scope = ScopedSymbolTable(
        #     scope_name=block_symbol,
        #     scope_level=self.current_scope.scope_level + 1,
        #     enclosing_scope=self.current_scope
        # )
        #
        # self.current_scope = block_scope
        self.visit(node.stmt_list)
        #
        # print(block_scope)
        # self.current_scope = self.current_scope.enclosing_scope
        # print('LEAVE scope: %s' % block_symbol.name)

    def visit_ForNode(self, node: ForNode):
        self.visit(node.init)
        self.visit(node.to)
        # block_symbol = BlockSymbol('FOR BODY')
        # self.current_scope.define(block_symbol)
        #
        # print('ENTER scope: %s' % block_symbol)
        # block_scope = ScopedSymbolTable(
        #     scope_name=block_symbol,
        #     scope_level=self.current_scope.scope_level + 1,
        #     enclosing_scope=self.current_scope
        # )
        #
        # self.current_scope = block_scope
        self.visit(node.body)
        #
        # print(block_scope)
        # self.current_scope = self.current_scope.enclosing_scope
        # print('LEAVE scope: %s' % block_symbol.name)
