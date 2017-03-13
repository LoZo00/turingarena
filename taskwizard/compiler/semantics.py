from collections import namedtuple, OrderedDict

Variable = namedtuple("Variable", ["name", "type", "array_dimensions"])
GlobalVariable = namedtuple("GlobalVariable", [*Variable._fields, "is_input", "is_output"])
Parameter = namedtuple("Parameter", [*Variable._fields])
Function = namedtuple("Function", ["name", "return_type", "parameters"])
Main = namedtuple("Main", ["commands"])
Command = namedtuple("Command", [])
Interface = namedtuple("Interface", ["name", "variables", "functions", "callback_functions", "main"])
Task = namedtuple("Task", ["interfaces", "variables", "functions"])


class CallbackFunction(Function):
    is_callback = True


class Semantics:

    def start(self, ast):
        variables = OrderedDict()
        functions = OrderedDict()
        interfaces = OrderedDict()

        for variable in ast.variables:
            variables[variable.name] = variable
        for function in ast.functions:
            functions[function.name] = function
        for interface in ast.interfaces:
            interfaces[interface.name] = interface

        return Task(interfaces, variables, functions)

    def interface(self, ast):
        variables = OrderedDict()
        functions = OrderedDict()
        callback_functions = OrderedDict()
        main = None

        for declaration in ast.declarations:
            container = None
            if isinstance(declaration, Variable):
                container = variables
            elif isinstance(declaration, CallbackFunction):
                container = callback_functions
            elif isinstance(declaration, Function):
                container = functions
            elif isinstance(declaration, Main):
                main = declaration

            if container is not None:
                container[declaration.name] = declaration

        return Interface(ast.name, variables, functions, callback_functions, main)

    def variable(self, ast):
        return Variable(ast.name, ast.type, ast.array_dimensions)

    def array_dimension(self, ast):
        if ast.constant is not None:
            return ast.constant
        else:
            return ast.variable_reference

    def global_variable_declaration(self, ast):
        return GlobalVariable(
            *ast.variable,
            is_input=(ast.inout in ["in", "inout"]),
            is_output=(ast.inout in ["out", "inout"])
        )

    def function_declaration(self, ast):
        parameters = OrderedDict()

        for parameter in ast.parameters:
            parameters[parameter.name] = parameter

        return (CallbackFunction if ast.callback is not None else Function)(
            ast.name, ast.return_type, OrderedDict(parameters)
        )

    def parameter(self, ast):
        return Parameter(*ast.variable)

    def _default(self, ast):
        return ast
