from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from myParser import *

# Класс описывающий грамматику языка Pascal
class PascalGrammar:
    def __init__(self):
        self.parser = self._make_parser()

    def _make_parser(self):
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
        AND = pp.Literal('and')
        OR = pp.Literal('or')
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

        array_ident = ident + LBRACK + literal + RBRACK
        call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR

        group = (
                literal |
                call |
                array_ident |
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


        #simple_assign = ((ident | array_ident) + ASSIGN.suppress() + expr).setName('assign')
        # type_arr = ARRAY + LBRACK + num + pp.Literal("..").suppress() + num + RBRACK + OF + type_spec
        ident_list = ident + pp.ZeroOrMore(COMMA + ident)
        var_decl = ident_list + COLON + type_spec + SEMI
        array_decl = ident_list + COLON + ARRAY + LBRACK + literal + pp.Literal(
            "..").suppress() + literal + RBRACK + OF + type_spec + SEMI
        vars_decl = VAR + pp.ZeroOrMore(var_decl | procedure_decl | function_decl | array_decl)

        assign = pp.Optional(array_ident | ident) + ASSIGN.suppress() + expr
        simple_stmt = assign | call

        for_body = stmt | pp.Group(SEMI).setName('stmt_list')
        for_cond = assign + pp.Keyword("to").suppress() + literal

        if_ = pp.Keyword("if").suppress() + pp.ZeroOrMore(LPAR) + expr + pp.ZeroOrMore(RPAR) + pp.Keyword("then").suppress() \
              + stmt + pp.Optional(pp.Keyword("else").suppress() + stmt)
        while_ = pp.Keyword("while").suppress() + LPAR + expr + RPAR + pp.Keyword("do").suppress() + stmt
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
        procedure_decl << pp.Keyword("procedure").suppress() + ident + pp.ZeroOrMore(LPAR + params + RPAR) + SEMI + vars_decl + body + SEMI

        function_decl << pp.Keyword("function").suppress() + ident + pp.Optional(
            LPAR + params + RPAR) + COLON + type_spec + SEMI + \
        vars_decl + body + SEMI

        program = pp.Keyword("Program").suppress() + ident + SEMI + pp.Optional(vars_decl) + body + DOT

        start = program.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

        for var_name, value in locals().copy().items():
            if isinstance(value, pp.ParserElement):
                PascalParser.parse(var_name, value)

        return start


    def parse(self, prog: str) -> StmtListNode:
        return self.parser.parseString(str(prog))[0]
