class ExpressionBuilder:
    def build(self, e):
        return getattr(self, e.expression_type)(e)

    def int_literal(self, e):
        return f"{e.value}"

    def reference(self, e):
        subscripts = "".join(f"[{self.build(index)}]" for index in e.indices)
        return f"{e.variable_name}{subscripts}"


class CodeGen:
    def block_content(self, b):
        for s in b.statements:
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

    def input_statement(self, s):
        raise NotImplementedError

    def output_statement(self, s):
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

    def for_statement(self, s):
        raise NotImplementedError

    def loop_statement(self, s):
        raise NotImplementedError

    def any_statement(self, s):
        raise NotImplementedError

    def expression(self, e):
        return getattr(self, f"{e.expression_type}_expression")(e)

    def int_literal_expression(self, e):
        return f"{e.value}"

    def reference_expression(self, e):
        subscripts = "".join(f"[{self.expression(index)}]" for index in e.indices)
        return f"{e.variable_name}{subscripts}"