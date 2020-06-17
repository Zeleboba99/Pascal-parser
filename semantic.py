from nodes import *
from grammar import *
from symbols import *
from jasmin import CodeGenerator


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
        self.init_builtin_functions()
        self.last_index = 0

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

    def init_builtin_functions(self):
        self.define(BuiltinFunction('Read'))
        self.define(BuiltinFunction('ReadLn'))
        self.define(BuiltinFunction('Write'))
        self.define(BuiltinFunction('WriteLn'))

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

    def get_level_scope(self, name) -> int:
        cur_scope = self
        while cur_scope is not None:
            symbol = self._symbols.get(name)
            if symbol is not None:
                return cur_scope.scope_level
            else:
                cur_scope = cur_scope.enclosing_scope
        return 0


class SemanticAnalyzer(NodeVisitor):
    def __init__(self, generator: CodeGenerator):
        self.generator = generator
        self.arrays_init = ''
        self.assemblerDict = {'integer':'I', 'char':'C','boolean':'Z'}
        self.dictionary = {'int':'integer', 'str':'char','bool':'boolean'}
        self.BinOpArgTypes = {
            'ADD':['integer','char'],
            'SUB':['integer'],
            'MUL':['integer'],
            'DIVISION':['integer'],
            'DIV':['integer'],
            'MOD':['integer'],
            'GE':['integer','char'],
            'LE':['integer','char'],
            'NEQUALS':['integer','char','boolean'],
            'EQUALS':['integer','char','boolean'],
            'GT':['integer','char'],
            'LT': ['integer', 'char'],
            'LOGICAL_AND':['boolean'],
            'LOGICAL_OR':['boolean']}

        self.BinOpReturnTypes = {
            'ADD': ['integer', 'char'],
            'SUB': ['integer'],
            'MUL': ['integer'],
            'DIVISION': ['integer'],
            'DIV': ['integer'],
            'MOD': ['integer'],
            'GE': ['boolean'],
            'LE': ['boolean'],
            'NEQUALS': ['boolean'],
            'EQUALS': ['boolean'],
            'GT': ['boolean'],
            'LT': ['boolean'],
            'LOGICAL_AND': ['boolean'],
            'LOGICAL_OR': ['boolean']}
        self.current_scope = None

    #convert type name to a correct format
    def __changeType(self,type) -> str:
        for key in self.dictionary:
            if type == key :
                return self.dictionary[key]
        return type

    def __typeChecker(self, type1, type2):
        if(type1 is None or type2 is None):
            return True
        if type1 == type2:
            return True
        for key in self.dictionary:
            if(type1 == key and type2 == self.dictionary[key] or type2==key and type1==self.dictionary[key]):
                return True
        return False

    def __isBinaryArgsValid(self, binOP, type_var):
        for key in self.BinOpArgTypes:
            if(binOP == key and type_var in self.BinOpArgTypes[key]):
                return True
        return False

    def __BinaryReturningType(self,binOP,type_var)->str:
        for key in self.BinOpReturnTypes:
            if key == binOP:
                if len(self.BinOpReturnTypes[key]) == 1:
                    return self.BinOpReturnTypes[key][0]
                else:
                    return type_var


    def visit_BinOpNode(self, node: BinOpNode):
        type_arg1 = self.visit(node.arg1)
        type_arg2 = self.visit(node.arg2)
        node.jbc(self.generator)

        if (not isinstance(node.arg1, BinOpNode)) or not (isinstance(node.arg2, BinOpNode)):
            if type_arg1 is not None and not self.__typeChecker(type_arg1, type_arg2):
                raise Exception("Incompatible types in line: ")
            type_arg1 = self.__changeType(type_arg1)
            type_arg2 = self.__changeType(type_arg2)
            if not self.__isBinaryArgsValid(node.op.name, type_arg1):
                raise Exception(
                    "Operation {op} not supported for types {t1} and {t2}"
                        .format(op=node.op.name, t1=type_arg1, t2=type_arg2))
            return self.__BinaryReturningType(node.op.name, type_arg1)

    def visit_IdentNode(self, node: IdentNode):
        var_name = node.name
        var_symbol = self.current_scope.lookup(var_name)

        if var_symbol.is_field:
            self.generator.add('getstatic {0}/{1} {2}'.format(self.global_scope.scope_name, var_name, self.assemblerDict[var_symbol.type.name]))
        else:
            self.generator.add('{0}load_{1}'.format(self.assemblerDict[var_symbol.type.name].lower(), var_symbol.index))

        if var_symbol is None:
            raise Exception("Symbol(identifier) not found '%s'" % var_name)
        return var_symbol.type.name

    def visit_LiteralNode(self, node: LiteralNode):
        node.jbc(self.generator)
        return type(node.value).__name__

    def visit_ProgramNode(self, node: ProgramNode):
        print('ENTER scope: global')
        self.global_scope = ScopedSymbolTable(
            scope_name=node.prog_name,
            scope_level=1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = self.global_scope
        node.jbc(self.generator)
        self.visit(node.vars_decl)
        self.generator.add('''.method                  public static main([Ljava/lang/String;)V
.limit stack          100
.limit locals         100''')
        self.generator.add(self.arrays_init)
        self.visit(node.stmt_list)
        print(self.current_scope)
        self.current_scope = self.current_scope.enclosing_scope
        self.generator.add('''   return
.end method''')
        print('LEAVE scope: global')

    def visit_VarsDeclNode(self, node: VarsDeclNode):
        for var_decl in node.var_decs:
            self.visit(var_decl)

    def visit_VarDeclNode(self, node: VarDeclNode):
        type_symbol = self.current_scope.lookup(node.vars_type.name)
        for ident in node.ident_list.idents:
            var_name = ident.name
            var_symbol = VarSymbol(var_name, type_symbol, index=self.current_scope.last_index)
            self.current_scope.last_index += 1
            #only for current scope
            if self.current_scope.lookup(var_name, current_scope_only=True):
                raise Exception(
                    "Duplicate identifier '%s' found" % var_name
                )
            self.current_scope.define(var_symbol)
            definition_level = self.current_scope.get_level_scope(var_name)
            if definition_level == 1:
                var_symbol.is_field = True
                self.generator.add('.field public static {0} {1}'.format(var_name, self.assemblerDict[type_symbol.name]))
            else:
                self.generator.add('')

    def visit_ArrayDeclNode(self, node: ArrayDeclNode):
        type = node.vars_type
        from_ = node.from_.literal
        to_ = node.to_.literal
        for ident in node.name.idents:
            arr_name = ident.name
            arr_symb = ArraySymbol(arr_name, type, from_, to_, index=self.current_scope.last_index)
            self.current_scope.last_index += 1
            if self.current_scope.lookup(arr_name, current_scope_only=True):
                raise Exception(
                    "Duplicate identifier '%s' found" % arr_name
                )
            self.current_scope.define(arr_symb)
            definition_level = self.current_scope.get_level_scope(arr_name)
            if definition_level == 1:
                arr_symb.is_field = True
                self.generator.add('.field public static {0} [{1}'.format(arr_name, self.assemblerDict[arr_symb.type.name]))
                self.arrays_init += 'ldc {0}\n'.format(to_)
                self.arrays_init += 'newarray int\n'
                self.arrays_init += 'putstatic {0}/{1} [{2}\n'.format(self.global_scope.scope_name, arr_name, self.assemblerDict[arr_symb.type.name])
            else:
                self.generator.add('')


    def visit_ArrayIdentNode(self, node : ArrayIdentNode):
        arr_name = node.name.name
        liter = int(node.literal.literal)
        arr_symbol = self.current_scope.lookup(arr_name)
        definition_level = self.current_scope.get_level_scope(arr_name)
        if definition_level == 1:
            self.generator.add('getstatic {0}/{1} [{2}'.format(self.global_scope.scope_name, arr_name, self.assemblerDict[arr_symbol.type.name]))
            self.visit(node.literal)
            self.generator.add('{0}aload'.format(self.assemblerDict[arr_symbol.type.name].lower()))

        if(liter < int(arr_symbol.from_) or liter > int(arr_symbol.to_)):
            raise Exception("Out of range '%s'" % liter)
        return arr_symbol.type.name

    def visit_BodyNode(self, node: BodyNode):
        self.visit(node.body)

    def visit_StmtListNode(self, node: StmtListNode):
        for stmt in node.exprs:
            self.visit(stmt)

    def visit_AssignNode(self, node: AssignNode):
        var = node.var
        val = node.val
        type_var = None



        if isinstance(var, ArrayIdentNode):
            var_name = var.name.name
            # type_var = self.visit(var)
            var_symbol = self.current_scope.lookup(var_name)
            self.generator.add('getstatic {0}/{1} [{2}'.format(self.global_scope.scope_name, var.name,
                                                               self.assemblerDict[var_symbol.type.name]))
            self.visit(var.literal)
        else:
            var_name = var.name
            var_symbol = self.current_scope.lookup(var_name)
        if var_symbol is None:
            raise Exception(
                "Undefined variable '%s' found" % var_name
            )
        type_visited = self.visit(val)
        if isinstance(var, ArrayIdentNode):
            self.generator.add('{0}astore'.format(self.assemblerDict[var_symbol.type.name].lower()))
        elif var_symbol.is_field:
            self.generator.add('putstatic {0}/{1} {2}'.format(self.global_scope.scope_name, var_name, self.assemblerDict[var_symbol.type.name]))
        else:
            self.generator.add('{0}store_{1}'.format(self.assemblerDict[var_symbol.type.name].lower(), var_symbol.index))

        if type_var is None:
            type_var = var_symbol.type.name
        if not self.__typeChecker(type_visited, type_var):
            raise Exception(
                "Wrong type '%s' found" % var_name
            )

    def visit_ProcedureDeclNode(self, node: ProcedureDeclNode):
        proc_name = node.proc_name.name
        proc_symbol = ProcedureSymbol(proc_name)
        self.current_scope.define(proc_symbol)

        print('ENTER scope: %s' % proc_name)
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )

        self.current_scope = procedure_scope
        for param in node.params.vars_list:
            param_type = self.current_scope.lookup(param.vars_type.name)
            for param_name in param.ident_list.idents:
                var_symbol = VarSymbol(param_name.name, param_type, index=self.current_scope.last_index)
                self.current_scope.last_index += 1
                self.current_scope.define(var_symbol)
                proc_symbol.params.append(var_symbol)

        params_sign = ''
        for p in proc_symbol.params:
            params_sign += self.assemblerDict[p.type.name]
        self.generator.add('.method public static {0}({1}){2}'.format(proc_name, params_sign, 'V'))
        self.generator.add('''.limit stack 100
        .limit locals 100''')

        for stmt in node.stmt_list.body.exprs:
            self.visit(stmt)

        self.generator.add('return')
        self.generator.add('.end method')
        print(procedure_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s' % proc_name)

    def visit_FunctionDeclNode(self, node: FunctionDeclNode):
        func_name = node.proc_name.name
        func_type = node.returning_type.name
        func_symbol = FunctionSymbol(func_name)
        func_symbol.type = func_type
        self.current_scope.define(func_symbol)

        print('ENTER scope: %s' % func_name)
        procedure_scope = ScopedSymbolTable(
            scope_name=func_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )

        self.current_scope = procedure_scope
        for param in node.params.vars_list:
            param_type = self.current_scope.lookup(param.vars_type.name)
            for param_name in param.ident_list.idents:
                var_symbol = VarSymbol(param_name.name, param_type, index=self.current_scope.last_index)
                self.current_scope.last_index += 1
                self.current_scope.define(var_symbol)
                func_symbol.params.append(var_symbol)

        params_sign = ''
        for p in func_symbol.params:
            params_sign += self.assemblerDict[p.type.name]
        self.generator.add('.method public static {0}({1}){2}'.format(func_name, params_sign,
                                                                      self.assemblerDict[node.returning_type.name]))
        self.generator.add('''.limit stack 100
.limit locals 100''')

        for stmt in node.stmt_list.body.exprs:
            self.visit(stmt)
        last_var = node.stmt_list.body.exprs[len(node.stmt_list.body.exprs)-1].var.name
        returning_var = self.current_scope.lookup(last_var)
        self.generator.add('{0}load_{1}'.format(self.assemblerDict[returning_var.type.name].lower(), returning_var.index))
        self.generator.add('{0}return'.format(self.assemblerDict[node.returning_type.name].lower()))
        self.generator.add('.end method')
        print(procedure_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: %s' % func_name)

    def visit_CallNode(self, node: CallNode):
        func_name = node.func.name
        func_symbol = self.current_scope.lookup(func_name)
        if func_symbol is None:
            raise Exception(
                "Undefined function '%s' " % func_name
            )
        #TODO builtin vs proc and func
        if (isinstance(func_symbol, FunctionSymbol) or isinstance(func_symbol, ProcedureSymbol)):
            if(len(node.params) != len(func_symbol.params)):
                raise Exception(
                    "Wrong number of parameters specified for call to '%s' " % func_name
                )
        if func_name == 'WriteLn' or func_name == 'Write':
            self.generator.add('getstatic             java/lang/System/out Ljava/io/PrintStream;')
        for param in node.params:
            self.visit(param)

        if func_name == 'WriteLn' or func_name == 'Write':
            arguments = ''
            for p in node.params:
                if isinstance(p, LiteralNode):
                    arguments += self.assemblerDict[self.dictionary[type(p.value).__name__]]
                elif isinstance(p, IdentNode):
                    arguments += self.assemblerDict[self.current_scope.lookup(p.name).type.name]
            self.generator.add('''invokevirtual         java/io/PrintStream/println(I)V''')
        elif func_name == 'ReadLn' or func_name == 'Read':
            self.generator.add('getstatic java/lang/System/in Ljava/io/InputStream;')
            arguments = ''
            store_instuctions = ''
            for p in node.params:
                symb = self.current_scope.lookup(p.name)
                arguments += self.assemblerDict[symb.type.name]
                if symb.is_field:
                    store_instuctions += 'putstatic {0}/{1} {2}'.format(self.global_scope.scope_name, symb.name,
                                                                      self.assemblerDict[symb.type.name])
                else:
                    store_instuctions += '{0}store_{1}'.format(
                        self.assemblerDict[self.current_scope.lookup(p.name).type.name].lower(),
                        self.current_scope.lookup(p.name).index)
            self.generator.add('invokevirtual java/io/InputStream/read(){0}'.format(arguments))
            self.generator.add(store_instuctions)
        else:
            params_sign = ''
            for p in func_symbol.params:
                params_sign += self.assemblerDict[p.type.name]
            self.generator.add('invokestatic {0}/{1}({2}){3}'.format(self.global_scope.scope_name, func_name, params_sign,self.assemblerDict[func_symbol.type]))
        return func_symbol.type

    def visit_IfNode(self, node: IfNode):
        type_cond = self.visit(node.cond)
        if_index = self.generator.last_index
        node.jbc(self.generator, index=if_index)
        if (type_cond != 'boolean'):
            raise Exception(
                "Wrong type of if condition '%s' " % type_cond
            )
        self.visit(node.then_stmt)
        self.generator.add('goto endif_{}'.format(if_index))

        self.generator.last_index += 1
        if node.else_stmt:
            self.generator.add('else_{}:'.format(if_index))
            self.visit(node.else_stmt)
        self.generator.add('endif_{}:'.format(if_index))


    def visit_WhileNode(self, node: WhileNode):
        while_index = self.generator.last_index
        self.generator.last_index += 1
        self.generator.add('while_{}:'.format(while_index))
        type_cond = self.visit(node.cond)
        self.generator.add('if_icmp{0} done_{1}'.format(str(node.cond.op.name).lower(), while_index))
        if type_cond != 'boolean':
            raise Exception(
                "Wrong type of while condition '%s' " % type_cond
            )
        self.visit(node.stmt_list)
        self.generator.add('goto while_{}'.format(while_index))
        self.generator.add('done_{}:'.format(while_index))

    #TODO check type of node.init
    def visit_ForNode(self, node: ForNode):
        for_index = self.generator.last_index
        type_init = self.visit(node.init)
        type_to = self.visit(node.to)
        if (type_to != 'int'):
            raise Exception(
                "Wrong type of for condition '%s'" % type_to
            )
        self.visit(node.body)
