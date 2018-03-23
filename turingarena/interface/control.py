from turingarena.common import ImmutableObject
from turingarena.interface.body import Body, ExitCall
from turingarena.interface.context import StaticContext
from turingarena.interface.driver.commands import Exit
from turingarena.interface.exceptions import InterfaceExit
from turingarena.interface.executable import ImperativeStatement, Instruction
from turingarena.interface.expressions import Expression
from turingarena.interface.type_expressions import ScalarType
from turingarena.interface.variables import Variable


class ExitStatement(ImperativeStatement):
    __slots__ = []

    def generate_instructions(self, context):
        yield ExitInstruction()
        raise InterfaceExit

    def first_calls(self):
        return {ExitCall}


class ExitInstruction(Instruction):
    __slots__ = []

    def on_request_lookahead(self, request):
        assert isinstance(request, Exit)

    def on_generate_response(self):
        return []


class IfStatement(ImperativeStatement):
    __slots__ = []

    @property
    def condition(self):
        return Expression.compile(self.ast.condition)

    @property
    def then_body(self):
        return Body(self.ast.then_body)

    @property
    def else_body(self):
        if self.ast.else_body is None:
            return None
        return Body(self.ast.then_body)

    def generate_instructions(self, context):
        condition = self.condition.evaluate_in(context)
        if not condition.is_resolved():
            # FIXME: use a stricter logic here
            if self.then_body.is_possible_branch(context):
                condition.resolve(1)
            else:
                condition.resolve(0)

        if condition.get():
            yield from self.then_body.generate_instructions(context)
        elif self.else_body is not None:
            yield from self.else_body.generate_instructions(context)

    def check_variables(self, initialized_variables, allocated_variables):
        self.condition.check_variables(initialized_variables, allocated_variables)
        self.then_body.check_variables(initialized_variables, allocated_variables)
        if self.else_body:
            self.else_body.check_variables(initialized_variables, allocated_variables)

    def first_calls(self):
        return self.then_body.first_calls() | (
            {None} if self.else_body is not None else
            self.else_body.first_calls()
        )


class ForIndex(ImmutableObject):
    __slots__ = ["variable", "range"]


class ForStatement(ImperativeStatement):
    __slots__ = []

    @property
    def index(self):
        ast = self.ast.index
        return ForIndex(
            variable=Variable(value_type=ScalarType(int), name=ast.declarator.name),
            range=Expression.compile(ast.range),
        )

    @property
    def body(self):
        return Body(self.ast.body)

    def validate(self, context):
        body, inner_context = self.contextualized_body(context)
        body.validate(inner_context)

    def contextualized_body(self, context):
        return self.body, StaticContext(
            declared_callbacks=context.declared_callbacks,
            global_variables=context.global_variables,
            functions=context.functions,
            variables=dict(context.variables, **{self.index.variable.name: self.index.variable}),
        )

    def generate_instructions(self, context):
        if not self.may_call():
            yield SimpleForInstruction(statement=self, context=context)
        else:
            yield from self.do_generate_instruction(context)

    def do_generate_instruction(self, context):
        size = self.index.range.evaluate_in(context=context).get()
        for i in range(size):
            inner_context = context.child({self.index.variable.name: self.index.variable})
            inner_context.bindings[self.index.variable] = i
            yield from self.body.generate_instructions(inner_context)

    def initialized_variables(self):
        return [self.index.variable]

    def may_call(self):
        return any(f is not None for f in self.body.first_calls())

    def check_variables(self, initialized_variables, allocated_variables):
        self.body.check_variables(initialized_variables, allocated_variables)

    def first_calls(self):
        return self.body.first_calls() | {None}


class SimpleForInstruction(Instruction):
    """
    Corresponds to a for-loop which does not perform any function call.
    This is seen as a single instruction so that it can be fully skipped
    in the preflight phase, when the number of iterations is not yet known.
    """

    __slots__ = ["statement", "context"]

    def on_communicate_with_process(self, connection):
        for instruction in self.statement.do_generate_instruction(self.context):
            instruction.on_communicate_with_process(connection)


class LoopStatement(ImperativeStatement):
    __slots__ = []

    @property
    def body(self):
        return Body(self.ast.body),

    def first_calls(self):
        return self.body.first_calls() | {None}
