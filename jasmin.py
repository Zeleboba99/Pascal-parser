from typing import List


class CodeLine:
    def __init__(self, code: str):
        self.code = code

    def __str__(self):
        return self.code


class CodeGenerator:
    def __init__(self):
        self.code_lines: List[CodeLine] = []
        self.last_index = 0

    def add(self, code: str):
        self.code_lines.append(CodeLine(code))

    @property
    def code(self) -> [str, ...]:
        code: List[str] = []
        for cl in self.code_lines:
            code.append(str(cl))
        return code
