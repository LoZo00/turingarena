from turingarena_impl.interface.exceptions import Diagnostic
from turingarena_impl.interface.tests.test_utils import assert_no_interface_errors, assert_interface_error


def test_variable_not_initialized():
    assert_interface_error("""
        main {
            var int a;
            write a;
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_variable_initialized():
    assert_no_interface_errors("""
        function f() -> int;
        main {
            var int a;
            call f() -> a;
            write a;
        }
    """)


def test_init_block_call():
    assert_no_interface_errors("""
        var int a;
        function f() -> int;
        init {
            call f() -> a;
        }
        main {
            write a;
        }
    """)


def test_call_on_itself():
    assert_interface_error("""
        function f(int a) -> int;
        main {
            var int a;
            call f(a) -> a;
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_variable_not_initialized_subscript():
    assert_interface_error("""
        main {
            var int a;
            var int[] A;
            read A[a];
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_variable_not_allocated():
    assert_interface_error("""
        main {
            var int[] a; 
            read a[0];
        }
    """, Diagnostic.Messages.VARIABLE_NOT_ALLOCATED, "a")


def test_variable_initialized_for():
    assert_no_interface_errors("""
        main {
            var int a;
            read a;
            for (i : a) {
                write i;
            }
        }
    """)


def test_variable_initialized_if():
    assert_no_interface_errors("""
        main {
             var int a; 
             read a;
             if (a) {
                write 1;
             } else {
                write 2;
            }
        }
    """)


def test_variable_in_if_body():
    assert_interface_error("""
        main {
            var int a;
            if (1) {
                write 1;
            } else {
                write a;
            }
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_variable_initialized_if_2():
    assert_no_interface_errors("""
        main {
             var int a;
             if (1) {
                 read a;
             } else {
                 read a;
             }
             write a;
        }
    """)


def test_variable_initialized_if_3():
    assert_interface_error("""
        main {
             var int a, b;
             if (1) {
                 read b;
             } else {
                 read a;
             }
             write a;
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_variable_initialized_call():
    assert_no_interface_errors("""
        function test(int a, int b) -> int;
        
        main {
            var int a, b, c;
            read a, b;
            call test(a, b) -> c;
            write c; 
        }
    """)


def test_variable_not_initialized_call():
    assert_interface_error("""
        function test(int a, int b) -> int;

        main {
            var int a, b, c;
            read a;
            call test(a, b) -> c;
            write c; 
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "b")


def test_local_variable():
    assert_no_interface_errors("""
        main {
            var int a;
            read a;
            write a;
        }
    """)


def test_local_variable_not_initialized():
    assert_interface_error("""
         main {
            var int a;
            write a;
        }
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_global_variables():
    assert_interface_error("""
        var int a;
        
        init {
        }
        
        main {
        }
    """, Diagnostic.Messages.GLOBAL_VARIABLE_NOT_INITIALIZED, "a")


def test_no_init_block():
    assert_interface_error("""
        var int a;
        
        main {}
    """, Diagnostic.Messages.INIT_BLOCK_MISSING)


def test_init_block():
    assert_no_interface_errors("""
        var int a;
        
        init {
            read a;
        }
        
        main {
            write a;
        }
    """)


def test_variable_not_declared():
    assert_interface_error("""
        main {
            write a;
        }
    """, Diagnostic.Messages.VARIABLE_NOT_DECLARED, "a")


def test_variable_redeclared():
    assert_interface_error("""
        var int a; 
        
        main {
            var int a;
        }
    """, Diagnostic.Messages.VARIABLE_REDECLARED, "a")


def test_variable_initialized_switch():
    assert_no_interface_errors("""
        main {
            var int a;
            switch (1) {
                case 1 {
                    read a;
                }
                case 2 {
                    read a;
                }
                default {
                    read a;
                }
            }
            write a;
        }    
    """)


def test_variable_not_initialized_switch():
    assert_interface_error("""
        main {
            var int a;
            switch (1) {
                case 1 {
                    read a;
                }
                case 2 {
                }
            }
            write a;
        }    
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")


def test_variable_not_initialized_switch_default():
    assert_interface_error("""
        main {
            var int a;
            switch (1) {
                case 1 {
                    read a;
                }
                default {
                }
            }
            write a;
        }    
    """, Diagnostic.Messages.VARIABLE_NOT_INITIALIZED, "a")
