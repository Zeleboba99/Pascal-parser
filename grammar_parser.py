from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from mel_ast import *


def _make_parser():
    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_
    ident = ppc.identifier.setName('ident')

    INT = pp.CaselessKeyword("integer")
    CHAR = pp.CaselessKeyword("char")
    BOOL = pp.CaselessKeyword("boolean")

    type_spec = INT | CHAR | BOOL

    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
    LBRACE, RBRACE = pp.CaselessKeyword("begin").suppress(), pp.CaselessKeyword("end").suppress()
    SEMI, COMMA, COLON = pp.Literal(';').suppress(), pp.Literal(',').suppress(), pp.Literal(':').suppress()
    ASSIGN = pp.Literal(':=')
    VAR = pp.CaselessKeyword("var").suppress()
    DOT = pp.Literal('.').suppress()

    ADD, SUB = pp.Literal('+'), pp.Literal('-')
    MUL, DIVISION = pp.Literal('*'), pp.Literal('/')
    MOD, DIV = pp.CaselessKeyword('mod'), pp.CaselessKeyword('div')
    AND = pp.Literal('&&')
    OR = pp.Literal('||')
    BIT_AND = pp.Literal('&')
    BIT_OR = pp.Literal('|')
    GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
    NEQUALS, EQUALS = pp.Literal('!='), pp.Literal('==')
    ARRAY = pp.CaselessKeyword("array").suppress()
    OF = pp.CaselessKeyword("of").suppress()

    add = pp.Forward()
    expr = pp.Forward()
    stmt = pp.Forward()
    stmt_list = pp.Forward()
    procedure_decl = pp.Forward()
    function_decl = pp.Forward()

    call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR

    group = (
        literal |
        call |
        ident |
        LPAR + expr + RPAR
    )

    mult = pp.Group(group + pp.ZeroOrMore((MUL | DIVISION | MOD | DIV) + group)).setName('bin_op')
    add << pp.Group(mult + pp.ZeroOrMore((ADD | SUB) + mult)).setName('bin_op')
    compare1 = pp.Group(add + pp.Optional((GE | LE | GT | LT) + add)).setName('bin_op')
    compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NEQUALS) + compare1)).setName('bin_op')
    logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('bin_op')
    logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('bin_op')

    expr << (logical_or)

    simple_assign = (ident + ASSIGN.suppress() + expr).setName('assign')
    #type_arr = ARRAY + LBRACK + num + pp.Literal("..").suppress() + num + RBRACK + OF + type_spec
    ident_list = ident + pp.ZeroOrMore(COMMA + ident)
    var_decl = ident_list + COLON + type_spec + SEMI
    array_decl = ident_list + COLON + ARRAY + LBRACK + literal + pp.Literal("..").suppress() + literal + RBRACK + OF + type_spec + SEMI
    vars_decl = VAR + pp.ZeroOrMore(var_decl | procedure_decl | function_decl | array_decl)


    assign = ident + ASSIGN.suppress() + expr
    simple_stmt = assign | call

    for_body = stmt | pp.Group(SEMI).setName('stmt_list')
    for_cond = assign + pp.Keyword("to").suppress() + literal

    #todo make LPAR and RPAR optional near condition
    if_ = pp.Keyword("if").suppress() + LPAR + expr + RPAR + pp.Keyword("then").suppress() \
          + stmt + pp.Optional(pp.Keyword("else").suppress() + stmt)
    while_ = pp.Keyword("while").suppress() + LPAR + expr + RPAR + pp.Keyword("do").suppress() + stmt
    #todo can`t parse SEMI after until
    repeat_ = pp.Keyword("repeat").suppress() + stmt_list + pp.Keyword("until").suppress() + LPAR + expr + RPAR
    for_ = pp.Keyword("for").suppress() + LPAR + for_cond + RPAR + pp.Keyword("do").suppress() + for_body


    comp_op = LBRACE + stmt_list + RBRACE + SEMI

    stmt << (
        if_ |
        for_ |
        while_ |
        repeat_ |
        comp_op |
        simple_stmt + SEMI
    )

    stmt_list << (pp.ZeroOrMore(stmt + pp.ZeroOrMore(SEMI)))

    body = LBRACE + stmt_list + RBRACE
    params = pp.ZeroOrMore(ident + pp.ZeroOrMore(COMMA + ident) + COLON + type_spec + SEMI) + \
             (ident + pp.ZeroOrMore(COMMA + ident) + COLON + type_spec)
    procedure_decl << pp.Keyword("procedure").suppress() + ident + pp.Optional(LPAR + params + RPAR) + SEMI +\
                        vars_decl + body + SEMI

    function_decl << pp.Keyword("function").suppress() + ident + pp.Optional(LPAR + params + RPAR) + SEMI + \
                        vars_decl + body + SEMI

    program = pp.Keyword("Program").suppress() + ident + SEMI + vars_decl + body + DOT

    start = program.ignore(pp.cStyleComment).ignore(pp.dblSlashComment)  + pp.StringEnd()


    def set_parse_action_magic(rule_name: str, parser: pp.ParserElement)->None:
        if rule_name == rule_name.upper():
            return
        if getattr(parser, 'name', None) and parser.name.isidentifier():
            rule_name = parser.name
        if rule_name in ('bin_op', ):
            def bin_op_parse_action(s, loc, tocs):
                node = tocs[0]
                if not isinstance(node, AstNode):
                    node = bin_op_parse_action(s, loc, node)
                for i in range(1, len(tocs) - 1, 2):
                    secondNode = tocs[i + 1]
                    if not isinstance(secondNode, AstNode):
                        secondNode = bin_op_parse_action(s, loc, secondNode)
                    node = BinOpNode(BinOp(tocs[i]), node, secondNode)
                return node
            parser.setParseAction(bin_op_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls)
                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        return cls(*tocs)
                    parser.setParseAction(parse_action)

    for var_name, value in locals().copy().items():
        if isinstance(value, pp.ParserElement):
            set_parse_action_magic(var_name, value)

    return start


parser = _make_parser()


def parse(prog: str)->StmtListNode:
    return parser.parseString(str(prog))[0]


