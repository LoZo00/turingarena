from turingarena_impl.interface.exceptions import Diagnostic
from turingarena_impl.interface.tests.test_utils import assert_interface_error, assert_no_interface_errors


def test_missing_local_flush():
    assert_interface_error("""
        main {
            var int a;
            write 5;
            read a;
        }
    """, Diagnostic.Messages.MISSING_FLUSH)


def test_missing_flush_for():
    assert_interface_error("""
        main {
            var int a;
            
            for (i : 5) {
                write 4;
            }
            
            read a;
        }
    """, Diagnostic.Messages.MISSING_FLUSH)


def test_missing_flush_for_2():
    assert_interface_error("""
        main {
            var int a;

            for (i : 5) {
                read a;
                write 4;
            }
        }
    """, Diagnostic.Messages.MISSING_FLUSH)


def test_missing_flush_for_3():
    assert_interface_error("""
        main {
            var int a, b;

            for (i : 5) {
                flush;
                read a;
                write 4;
            }
            read b;
        }
    """, Diagnostic.Messages.MISSING_FLUSH)


def test_for():
    assert_no_interface_errors("""
        main {
            var int a;

            for (i : 5) {
                read a;
                write 4;
                flush;
            }
            write 4;
        }
    """)


def test_missing_flush_if():
    assert_interface_error("""
        main {
            var int a, b;
            read a;
            if (a) {
                flush;
            } else {
                write 4;
            }
            
            read b;
        }
    """, Diagnostic.Messages.MISSING_FLUSH)


def test_missing_flush_if_2():
    assert_no_interface_errors("""
        main {
            var int a, b;
            read a;
            if (a) {
                flush;
            } else {
                write 4;
                flush;
            }

            read b;
        }
    """)


def test_missing_flush_init():
    assert_interface_error("""
        init {
            write 4;
        }
        
        main {
            var int a;
            read a;
        }
    """, Diagnostic.Messages.MISSING_FLUSH)
