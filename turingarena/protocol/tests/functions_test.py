import pytest

from turingarena.protocol.exceptions import ProtocolError
from turingarena.protocol.module import ProtocolSource
from turingarena.test_utils import algorithm


def test_function_no_arguments():
    protocol_text="""
                interface function_no_arguments {
                    function function_no_arguments();
                    main {
                        call function_no_arguments();
                    }
                }
            """
    source_mapping = {
            'c++': """
                void function_no_arguments() {
                }
            """,
            'python': """if True:
                def function_no_arguments():
                    pass
            """ }
    for language, source in source_mapping.items():
        with algorithm(
                source_text=source,
                language=language,
                protocol_text=protocol_text,
                interface_name="function_no_arguments",
        ) as impl:
            with impl.run() as (process, p):
                p.function_no_arguments()


def test_function_with_arguments():
    protocol_text="""
        interface function_with_arguments {
            function function_with_arguments(int a, int b);
            main {
                var int a, b;
                input a, b;
                call function_with_arguments(a, b);
            }
        }
    """

    source_mapping = {
            'c++' : """
                #include <cassert>
                void function_with_arguments(int a, int b) {
                    assert(a == 1 && b == 2);
                }
            """,
            'python':"""if True:
                def function_with_arguments(a,b):
                    assert a == 1 and b == 2
            """ }

    for language, source in source_mapping.items():
        with algorithm(
                source_text=source,
                language=language,
                protocol_text=protocol_text,
            interface_name="function_with_arguments",
        ) as impl:
            with impl.run() as (process, p):
                p.function_with_arguments(1, 2)

def test_function_return_value():
    protocol_text="""
        interface function_return_value {
            function function_return_value(int a) -> int;
            main {
                var int a, b;
                input a;
                call function_return_value(a) -> b;
                output b;
            }
        }
    """
    source_mapping = {
            'c++':"""
                #include <cassert>
                int function_return_value(int a) {
                    assert(a == 1);
                    return 2;
                }
            """,
            'python':"""if True:
                def function_return_value(a):
                    assert a == 1
                    return 2
            """ }

    for language, source in source_mapping.items():
        with algorithm(
                source_text=source,
                language=language,
                protocol_text=protocol_text,
                interface_name="function_return_value",
        ) as impl:
            with impl.run() as (process, p):
                assert p.function_return_value(1) == 2

def test_function_return_type_not_scalar():
    protocol_text = """
        interface function_return_type_not_scalar {
            function function_return_type_not_scalar() -> int[];
            main {}
        }
    """
    source = ProtocolSource(
        text=protocol_text,
        filename="<none>",
    )

    with pytest.raises(ProtocolError) as excinfo:
        source.compile()
    assert 'return type must be a scalar' in excinfo.value.get_user_message()
