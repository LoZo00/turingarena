from turingarena.common import indent_all, indent


def generate_skeleton_javascript(interface):
    for statement in interface.body.statements:
        yield
        yield from generate_skeleton_statement(statement, interface=interface)


def generate_template_javascript(interface):
    for statement in interface.body.statements:
        yield
        yield from generate_template_statement(statement, interface=interface)


def generate_skeleton_statement(statement, *, interface):
    generators = {
        "var": lambda: generate_var(statement),
        "function": lambda: [],
        "callback": lambda: generate_callback(statement, interface=interface),
        "main": lambda: generate_main(statement, interface=interface),
    }
    return generators[statement.statement_type]()


def generate_template_statement(statement, *, interface):
    generators = {
        "var": lambda: generate_global_var_template(statement),
        "function": lambda: generate_function_template(statement),
        "callback": lambda: generate_callback_template(statement, interface=interface),
        "main": lambda: [],
    }
    return generators[statement.statement_type]()


def generate_var(statement):
    for var in statement.variables:
        name = var.name
        var_type = build_type(var.value_type)
        yield f"var {name}; // {var_type}"


def generate_global_var_template(statement):
    names = ", ".join(v.name for v in statement.variables)
    yield f"// global var: {names}"


def generate_function_template(statement):
    fun = statement.function
    yield f"function {build_callable_declarator(fun)}" + "{"
    yield indent("// TODO")
    yield "}"


def generate_callback(statement, *, interface):
    callback = statement.callback
    yield f"function {build_callable_declarator(callback)}" + "{"
    yield indent(f"print('{callback.name}');")
    yield from indent_all(generate_block(callback.body, interface=interface))
    yield "}"


def generate_callback_template(statement, *, interface):
    yield f"// callback {statement.callback.name}"


def generate_main(statement, *, interface):
    yield 'function main() {'
    yield from indent_all(generate_block(statement.main.body, interface=interface))
    yield '}'


def generate_block(block, *, interface):
    for statement in block.statements:
        yield from generate_block_statement(statement, interface=interface)


def generate_block_statement(statement, *, interface):
    generators = {
        "var": lambda: generate_var(statement),
        "alloc": lambda: generate_alloc(statement),
        "input": lambda: generate_input(statement),
        "output": lambda: generate_output(statement),
        "checkpoint": lambda: ["print(0);"],
        "flush": lambda: ["// flush"],
        "call": lambda: generate_call(statement, interface=interface),
        "for": lambda: generate_for(statement, interface=interface),
        "if": lambda: generate_if(statement, interface=interface),
        "exit": lambda: ["exit(0);"],
        "return": lambda: [f"return {build_expression(statement.value)};"],
    }
    return generators[statement.statement_type]()


def generate_alloc(statement):
    for argument in statement.arguments:
        arg = build_expression(argument)
        size = build_expression(statement.size)
        yield f"var {arg} = Array({size});"


def generate_call(statement, *, interface):
    function_name = statement.function.name
    yield f"__load_source__()"
    parameters = ", ".join(build_expression(p) for p in statement.parameters)
    if statement.return_value is not None:
        return_value = build_expression(statement.return_value)
        yield f"{return_value} = {function_name}({parameters});"
    else:
        yield f"{function_name}({parameters});"
    if interface.signature.callbacks:
        yield r"""print("return");"""


def generate_output(statement):
    args = ', '.join(build_expression(v) for v in statement.arguments)
    yield f'print({args});'


def generate_input(statement):
    format_string = ''.join(build_format_string(v) for v in statement.arguments)
    args = ', '.join(build_expression(v) for v in statement.arguments)
    yield f'[{args}] = scanf("{format_string}");'


def generate_if(statement, *, interface):
    condition = build_expression(statement.condition)
    yield f"if ({condition})" " {"
    yield from indent_all(generate_block(statement.then_body, interface=interface))
    if statement.else_body is not None:
        yield "} else {"
        yield from indent_all(generate_block(statement.else_body, interface=interface))
    yield "}"


def generate_for(statement, *, interface):
    index_name = statement.index.variable.name
    size = build_expression(statement.index.range)
    yield f"for (var {index_name} = 0; {index_name} < {size}; {index_name}++)" " {"
    yield from indent_all(generate_block(statement.body, interface=interface))
    yield "}"


def build_callable_declarator(callable):
    signature = callable.signature
    arguments = ', '.join(build_parameter(p) for p in signature.parameters)
    return f"{callable.name}({arguments})"


def build_parameter(parameter):
    return f'{parameter.name}'


def build_subscript(expression):
    array = build_expression(expression.array)
    index = build_expression(expression.index)
    return f"{array}[{index}]"


def build_expression(expression):
    builders = {
        "int_literal": lambda: f"{expression.value}",
        "reference": lambda: f"{expression.variable.name}",
        "subscript": lambda: build_subscript(expression),
    }
    return builders[expression.expression_type]()


def build_type(t):
    builders = {
        "scalar": lambda: f"{build_format(t.base_type)}",
        "array": lambda: f"List[{build_type(t.item_type)}]",
    }
    return builders[t.meta_type]()


def build_format(t):
    return {
        int: "int",
    }[t]


def build_format_string(expr):
    return {
        int: "%d",
    }[expr.value_type.base_type]