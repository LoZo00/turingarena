from turingarena_impl.interface.tests.test_utils import define_algorithm


interface_text = """
    function test() -> int;
    main {
        var int o;
        call test() -> o;
        write o;
    }
"""


def test_sandbox_smoke():
    with define_algorithm(
            interface_text=interface_text,
            language_name="python",
            source_text="""if True:
                def test():
                    return 3
            """,
    ) as algo:
        with algo.run() as p:
            assert p.call.test() == 3
