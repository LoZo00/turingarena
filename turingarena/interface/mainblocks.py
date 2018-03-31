from turingarena.interface.exceptions import Diagnostic
from turingarena.interface.statement import Statement
from turingarena.interface.block import ImperativeBlock


class EntryPointStatement(Statement):
    __slots__ = []

    @property
    def body(self):
        return ImperativeBlock(ast=self.ast.body, context=self.context.create_local())

    def validate(self):
        yield from self.body.validate()

    @property
    def context_after(self):
        new_context = self.body.context_after
        return self.context.with_initialized_variables(new_context.initialized_variables)\
            .with_allocated_variables(new_context.allocated_variables)\
            .with_flushed_output(new_context.has_flushed_output)


class InitStatement(EntryPointStatement):
    __slots__ = []

    def validate(self):
        super().validate()

        new_context = self.context_after
        for var in self.context.global_variables:
            if var not in new_context.initialized_variables:
                yield Diagnostic(f"global variable {var.name} not initialized in init block", parseinfo=self.ast.parseinfo)


class MainStatement(EntryPointStatement):
    __slots__ = []

