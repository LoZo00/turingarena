from pytest import approx

from turingarena.test_utils import define_interface, define_algorithm


def test_get_time_memory_usage():
    with define_interface("""
        function test(int i) -> int;
        main {
            var int i1, i2, o1, o2;
            input i1;
            call test(i1) -> o1;
            output o1;
            flush;
            input i2;
            call test(i2) -> o2;
            output o2;
        }
    """) as iface:
        with define_algorithm(
                interface=iface,
                language="c++",
                source_text="""
                    int test(int i) {
                        char x[1024 * 1024];
                        for(int j = 0; j < 100 * 1000 * 1000; j++) {
                            i = x[j%1024] = j^i^x[j%1024];
                        }
                        return i;
                    }
                """
        ) as algo:
            with algo.run() as (process, proxy):
                with process.section() as section1:
                    proxy.test(1)
                info1 = process.sandbox.get_info()
                with process.section() as section2:
                    proxy.test(2)
                info2 = process.sandbox.get_info()

    assert 0 < section1.time_usage == info1.time_usage < 0.5
    assert 0 < section2.time_usage < 0.5

    assert section1.time_usage + section2.time_usage == approx(info2.time_usage)

    assert 1024 * 1024 < info1.memory_usage < 2 * 1024 * 1024
    assert info2.memory_usage == 0
