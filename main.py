import os
from grammar import *
from semantic import *
from file_helper import *


def main():
    prog = FileHelper.read_from_file('resources/input_program_3.txt')
    g = PascalGrammar()
    prog = g.parse(prog)
    print(*prog.tree, sep=os.linesep)
    code_generator = CodeGenerator()
    symb_table_builder = SemanticAnalyzer(code_generator)
    symb_table_builder.visit(prog)
    print(*symb_table_builder.generator.code, sep=os.linesep)
    FileHelper.write_to_file('resources/jasmin_res.j', '\n'.join(symb_table_builder.generator.code))


if __name__ == "__main__":
    main()
