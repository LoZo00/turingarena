from collections import OrderedDict

from taskwizard.definition.common import Identifier
from taskwizard.definition.declarations import named_definitions
from taskwizard.definition.function import FunctionDefinition
from taskwizard.definition.protocol import Protocol
from taskwizard.definition.syntax import AbstractSyntaxNode
from taskwizard.definition.variable import VariableDefinition


class InterfaceDefinition(AbstractSyntaxNode):

    grammar = """
        interface_definition =
            'interface' name:identifier '{'

            declarations:{
            | variable_declaration
            | function_declaration
            | protocol_declaration
            }*

            '}'
        ;
    """
    grammar_deps = lambda: [Identifier, VariableDefinition, FunctionDefinition, Protocol.Definition]

    def get_variable_definitions(self):
        return [d for d in self.declarations if isinstance(d, VariableDefinition)]

    def get_function_definitions(self):
        return [d for d in self.declarations if isinstance(d, FunctionDefinition) and not d.is_callback()]

    def get_callback_function_definitions(self):
        return [d for d in self.declarations if isinstance(d, FunctionDefinition) and d.is_callback()]

    def get_protocol_definitions(self):
        return [d for d in self.declarations if isinstance(d, Protocol.Definition)]


class Interface:

    def __init__(self, definition):
        self.definition = definition
        self.name = definition.name
        self.variables = OrderedDict(
                (d.name, d) for d in definition.get_variable_definitions()
        )
        self.functions = named_definitions(definition.get_function_definitions())
        self.callback_functions = named_definitions(definition.get_callback_function_definitions())
        self.named_protocols = OrderedDict(
                (d.name, Protocol(d)) for d in definition.get_protocol_definitions()
            if hasattr(d, "name")
        )
        self.main_protocol = (
            [Protocol(d) for d in definition.get_protocol_definitions() if not hasattr(d, "name")] + [None]
        )[0]

    def get_arrays_to_allocate(self, protocol):
        return protocol.get_arrays_to_allocate(self.variables)