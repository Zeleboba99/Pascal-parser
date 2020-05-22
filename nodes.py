from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
from enum import Enum
import inspect

# Абстрактный класс - узел AST-дерева
# Все рализованные далее классы узлов являются потомками этого класса
class AstNode(ABC):
    def __init__(self, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__()
        self.row = row
        self.line = line
        for k, v in props.items():
            setattr(self, k, v)

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs_temp = self.childs
        for i, child in enumerate(childs_temp):
            ch0, ch = '├', '│'
            if i == len(childs_temp) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class ExprNode(AstNode):
    pass

# Узел содержащий значение переменной и ее типа
class LiteralNode(ExprNode):
    def __init__(self, literal: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.literal = literal
        self.value = eval(literal)

    def __str__(self) -> str:
        return '{0} ({1})'.format(self.literal, type(self.value).__name__)


# Узел содержащий название переменной
class IdentNode(ExprNode):
    # k,j..
    def __init__(self, name: str, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


# Узел содержащий элементы массива
class ArrayIdentNode(ExprNode):
    def __init__(self, name: IdentNode, literal: LiteralNode, row: Optional[int] = None, line: Optional[int] = None,
                 **props):
        super().__init__(row=row, line=line, **props)
        self.name = name;
        self.literal = literal;

    # @property
    # def childs(self) -> Tuple[IdentNode, LiteralNode]:
    #     return self.name, self.literal

    def __str__(self) -> str:
        return '{0} [{1}]'.format(self.name, self.literal)

# Перечисление содержащее символы для бинарных операций
class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIVISION = '/'
    DIV = 'div'
    MOD = 'mod'
    GE = '>='
    LE = '<='
    NEQUALS = '<>'
    EQUALS = '='
    GT = '>'
    LT = '<'
    LOGICAL_AND = 'and'
    LOGICAL_OR = 'or'

# Узел реализующий бинарную операцию
class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def childs(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class StmtNode(ExprNode):
    pass

# Узел содержащий список переменных определенного типа
class IdentListNode(StmtNode):
    def __init__(self, *idents: Tuple[IdentNode, ...], row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.idents = idents

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.idents

    def __str__(self) -> str:
        return "idents"

# Узел содержащий тип переменной или списка переменных
class TypeSpecNode(StmtNode):
    def __init__(self, name: str, row: Optional[int] = None, line: Optional[int] = None, **props):
        super(TypeSpecNode, self).__init__(row=row, line=line, **props)
        self.name = name

    def __str__(self) -> str:
        return self.name


class VarDeclNode(StmtNode):
    def __init__(self, ident_list: IdentListNode, vars_type: TypeSpecNode,  # *vars_list: Tuple[AstNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.ident_list = ident_list
        self.vars_type = vars_type

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return (self.ident_list,) + (self.vars_type,)

    def __str__(self) -> str:
        return 'var_dec'

# Узел реализующий объявление массива, переменную, размерность и тип
# name идентификатор массива
# from_ индекс первого элемента массива
# to_ индекс последнего элемента массива
# vars_type тип к которому относится массив
class ArrayDeclNode(StmtNode):
    def __init__(self, name: Tuple[AstNode, ...],
                 from_: LiteralNode, to_: LiteralNode, vars_type: TypeSpecNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = name
        self.from_ = from_
        self.to_ = to_
        self.vars_type = vars_type

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        # return self.vars_type, (*self.vars_list)
        return (self.vars_type,) + (self.name,) + (self.from_,) + (self.to_,)

    def __str__(self) -> str:
        return 'arr_decl'

# Узел реализующий раздел описания переменных
class VarsDeclNode(StmtNode):
    def __init__(self, *var_decs: Tuple[VarDeclNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var_decs = var_decs

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.var_decs

    def __str__(self) -> str:
        return 'var'

# Узел реализующий вызов функций или процедур
class CallNode(StmtNode):
    def __init__(self, func: IdentNode, *params: Tuple[ExprNode],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.func = func
        self.params = params

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        # return self.func, (*self.params)
        return (self.func,) + self.params

    def __str__(self) -> str:
        return 'call'

# Узел реализующий операцию присваивания переменной var значения val
class AssignNode(StmtNode):
    def __init__(self, var,
                 val: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var = var
        self.val = val

    # def childs(self) -> Tuple[IdentNode, ExprNode]:
    @property
    def childs(self):
        return self.var, self.val

    def __str__(self) -> str:
        return ':='

# Узел реализующий условный оператор if
# cond логическое выражение внутри if
# then_stmt выражение выполняющееся при true в cond
# else_stmt выражение выполняющееся при false в cond
class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.then_stmt) + ((self.else_stmt,) if self.else_stmt else tuple())

    def __str__(self) -> str:
        return 'if'

# Узел реализующий цикл while
# cond логическое выражение внутри while
# stmt_list операторы в теле цикла
class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, stmt_list: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.stmt_list = stmt_list

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.stmt_list)

    def __str__(self) -> str:
        return 'while'

# в данный момент в разработке
class RepeatNode(StmtNode):
    def __init__(self, stmt_list: StmtNode, cond: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.stmt_list = stmt_list
        self.cond = cond

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.stmt_list, self.cond)

    def __str__(self) -> str:
        return 'repeat'

# Узел описывающий цикл с параметром for
# init начальное значение
# to конечное значение
# body оператор в теле цикла
class ForNode(StmtNode):
    def __init__(self, init: Union[StmtNode, None],
                 to,
                 body: Union[StmtNode, None],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.init = init if init else _empty
        self.to = to
        self.body = body if body else _empty

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.init, self.to, self.body

    def __str__(self) -> str:
        return 'for'

# Узел содержащий список выражений
class StmtListNode(StmtNode):
    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.exprs = exprs

    @property
    def childs(self) -> Tuple[StmtNode, ...]:
        return self.exprs

    def __str__(self) -> str:
        return '...'

# Узел являющийся телом (внутренности между begin и end) содержащий список выражений
class BodyNode(ExprNode):
    def __init__(self, body: Tuple[StmtNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.body = body

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (self.body,)

    def __str__(self) -> str:
        return 'Body'

# Узел содержащий параметры функции, процедуры
#TODO переделать, параметры считываются неправильно
class ParamsNode(StmtNode):
    def __init__(self, *vars_list: VarDeclNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.vars_list = vars_list if vars_list else _empty

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.vars_list

    def __str__(self) -> str:
        return 'params'

# Узел описывающий программу
# prog_name название программы
# vars_decl раздел описаний
# stmt_list тело программы
class ProgramNode(ExprNode):
    def __init__(self, prog_name: Tuple[AstNode, ...], vars_decl: Tuple[AstNode, ...],
                 stmt_list: Tuple[AstNode, ...],
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.prog_name = prog_name
        self.vars_decl = vars_decl
        self.stmt_list = stmt_list

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (self.prog_name,) + (self.vars_decl,) + (self.stmt_list,)

    def __str__(self) -> str:
        return 'Program'

# Узел содержщий объявление процедуры
# число параметров *args зависит от того, объявили мы процедуру с параметрами или без
class ProcedureDeclNode(ExprNode):
    def __init__(self, *args, **props):
        super().__init__(row=_empty, line=_empty, **props)
        self.proc_name = args[0]
        if(len(args) == 4):
            self.params = args[1]
            self.vars_decl = args[2]
            self.stmt_list = args[3]
        else:
            self.params = _empty
            self.vars_decl = args[1]
            self.stmt_list = args[2]

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (self.proc_name,) + (self.params,) + (self.vars_decl,) + (self.stmt_list,)


    def __str__(self) -> str:
        return 'procedure'


# Узел содержщий объявление функции
# число параметров *args зависит от того, объявили мы функцию с параметрами или без
class FunctionDeclNode(ExprNode):
    def __init__(self,*args,**props):
        super().__init__(row=_empty, line=_empty, **props)
        self.proc_name = args[0]
        if (len(args) == 5):
            self.params = args[1]
            self.returning_type = args[2]
            self.vars_decl = args[3]
            self.stmt_list = args[4]
        else:
            self.params = _empty
            self.returning_type = args[1]
            self.vars_decl = args[2]
            self.stmt_list = args[3]

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (self.proc_name,) + (self.params,) + (self.returning_type,) + (self.vars_decl,) + (self.stmt_list,)

    def __str__(self) -> str:
        return 'function'


_empty = StmtListNode()
