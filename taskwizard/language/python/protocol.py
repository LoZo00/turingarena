from taskwizard.generation.expressions import AbstractExpressionGenerator
from taskwizard.generation.scope import Scope
from taskwizard.generation.utils import indent_all, indent
from taskwizard.grammar import SyntaxVisitor
from taskwizard.language.python.expression import build_driver_expression


class BlockDriverGenerator(SyntaxVisitor):

    def __init__(self, scope):
        self.scope = scope

    def visit_local_declaration(self, declaration):
        for declarator in self.scope.process_declarators(declaration):
            yield "{name} = None".format(
                name=declarator.name,
            )

    def visit_input_statement(self, statement):
        yield "self.downward_pipe.print({arguments})".format(
            arguments=", ".join(
                build_driver_expression(self.scope, e)
                for e in statement.arguments
            )
        )

    def visit_output_statement(self, statement):
        yield "_values = self.upward_pipe.readline().split()"
        for i, argument in enumerate(statement.arguments):
            yield "{arg} = int(_values[{i}])".format(
                arg=build_driver_expression(self.scope, argument),
                i=i,
            )

    def visit_alloc_statement(self, statement):
        return []

    def visit_call_statement(self, statement):
        return []

    def visit_for_statement(self, statement):
        yield "for {index} in range({start}, {end}):".format(
            index=statement.index.declarator.name,
            start=build_driver_expression(self.scope, statement.index.range.start),
            end="1 + " + build_driver_expression(self.scope, statement.index.range.end),
        )
        new_scope = Scope(self.scope)
        new_scope.process_simple_declaration(statement.index)
        yield from indent_all(generate_driver_block(statement.block, new_scope))


def generate_driver_block(block, external_scope):
    generator = BlockDriverGenerator(external_scope)
    for item in block.block_items:
        yield from generator.visit(item)
