class CodeGen:
    __slots__ = ["interface"]

    def __init__(self, interface):
        self.interface = interface

    def write_to_file(self, file):
        for line in self.generate():
            if line is None:
                print("", file=file)
            else:
                print(line, file=file)

    def generate(self):
        yield from self.block_content(self.interface.body, indent=False)

    def block_content(self, b, indent=True):
        for s in b.synthetic_statements:
            if indent:
                yield from self.indent_all(self.statement(s))
            else:
                yield from self.statement(s)

    def statement(self, s):
        method_name = f"{s.statement_type}_statement"
        try:
            return getattr(self, method_name)(s)
        except NotImplementedError:
            return self.any_statement(s)

    def var_statement(self, s):
        raise NotImplementedError

    def function_statement(self, s):
        raise NotImplementedError

    def callback_statement(self, s):
        raise NotImplementedError

    def init_statement(self, s):
        raise NotImplementedError

    def main_statement(self, s):
        raise NotImplementedError

    def read_statement(self, s):
        raise NotImplementedError

    def write_statement(self, s):
        raise NotImplementedError

    def checkpoint_statement(self, s):
        raise NotImplementedError

    def flush_statement(self, s):
        raise NotImplementedError

    def break_statement(self, s):
        raise NotImplementedError

    def continue_statement(self, s):
        raise NotImplementedError

    def exit_statement(self, s):
        raise NotImplementedError

    def alloc_statement(self, s):
        raise NotImplementedError

    def return_statement(self, s):
        raise NotImplementedError

    def call_statement(self, s):
        raise NotImplementedError

    def if_statement(self, s):
        raise NotImplementedError

    def switch_statement(self, s):
        raise NotImplementedError

    def case_statement(self, s):
        raise NotImplementedError

    def for_statement(self, s):
        raise NotImplementedError

    def loop_statement(self, s):
        raise NotImplementedError

    def any_statement(self, s):
        return []

    def expression(self, e):
        return getattr(self, f"{e.expression_type}_expression")(e)

    def int_literal_expression(self, e):
        return f"{e.value}"

    def reference_expression(self, e):
        subscripts = "".join(f"[{self.expression(index)}]" for index in e.indices)
        return f"{e.variable_name}{subscripts}"

    @staticmethod
    def indent_all(lines):
        for line in lines:
            yield CodeGen.indent(line)

    @staticmethod
    def indent(line):
        if line is None:
            return None
        else:
            return "    " + line