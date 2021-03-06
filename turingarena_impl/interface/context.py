import logging
from collections import namedtuple

from turingarena_impl.interface.bindings import BindingStorage

logger = logging.getLogger(__name__)


class RootContext(namedtuple("RootContext", [])):
    __slots__ = []

    def create_inner(self):
        return StaticGlobalContext(
            functions=(),
            callbacks=(),
            locally_defined_variables=(),
            locally_allocated_variables=frozenset(),
            locally_initialized_variables=frozenset(),
            last_output_flushed=True
        )


class VariablesContextMixin:
    __slots__ = []

    def with_variables(self, variables):
        return self._replace(
            locally_defined_variables=self.locally_defined_variables + variables
        )

    def with_initialized_variables(self, variables):
        return self._replace(
            locally_initialized_variables=self.locally_initialized_variables | variables
        )

    def with_allocated_variables(self, variables):
        return self._replace(
            locally_allocated_variables=self.locally_allocated_variables | variables
        )

    def with_flushed_output(self, flush):
        return self._replace(last_output_flushed=flush)

    @property
    def has_flushed_output(self):
        return self.last_output_flushed

    @property
    def initialized_variables(self):
        return self.outer_initialized_variables | self.locally_initialized_variables

    @property
    def allocated_variables_mapping(self):
        return {
            var[0]: var[1]
            for var in self.allocated_variables
            if var
        }

    @property
    def allocated_variables(self):
        return self.outer_allocated_variables | self.locally_allocated_variables

    @property
    def variables(self):
        return self.outer_variables + self.locally_defined_variables

    @property
    def variable_mapping(self):
        return {v.name: v for v in self.variables}

    @property
    def outer_variables(self):
        return ()

    @property
    def outer_allocated_variables(self):
        return {None}

    @property
    def outer_initialized_variables(self):
        return {None}


class StaticGlobalContext(namedtuple("StaticGlobalContext", [
    "functions",
    "callbacks",
    "locally_defined_variables",
    "locally_initialized_variables",
    "locally_allocated_variables",
    "last_output_flushed",
]), VariablesContextMixin):
    @property
    def global_variables(self):
        return self.variables

    @property
    def function_map(self):
        return {f.name: f for f in self.functions}

    @property
    def callback_map(self):
        return {c.name: c for c in self.callbacks}

    def with_function(self, f):
        return self._replace(functions=self.functions + (f,))

    def with_callback(self, c):
        return self._replace(callbacks=self.callbacks + (c,))

    def create_local(self):
        return StaticLocalContext(
            global_context=self,
            outer_context=None,
            locally_defined_variables=(),
            locally_allocated_variables=frozenset(),
            locally_initialized_variables=frozenset(),
            last_output_flushed=self.last_output_flushed,
            index_variables=(),
            in_loop=False,
            has_break=False,
        )


class StaticLocalContext(namedtuple("StaticLocalContext", [
    "global_context",
    "outer_context",
    "locally_defined_variables",
    "locally_initialized_variables",
    "locally_allocated_variables",
    "last_output_flushed",
    "index_variables",
    "in_loop",
    "has_break",
]), VariablesContextMixin):
    @property
    def outer_initialized_variables(self):
        if self.outer_context:
            return self.outer_context.initialized_variables
        else:
            return self.global_context.initialized_variables

    @property
    def outer_allocated_variables(self):
        if self.outer_context:
            return self.outer_context.allocated_variables
        else:
            return self.global_context.allocated_variables

    @property
    def outer_variables(self):
        if self.outer_context:
            return self.outer_context.variables
        else:
            return self.global_context.variables

    def with_index_variable(self, variable):
        return self._replace(
            index_variables=self.index_variables + (variable,),
            locally_initialized_variables=self.locally_initialized_variables | {variable.variable},
            locally_defined_variables=self.locally_defined_variables + (variable.variable,),
        )

    def with_loop(self):
        return self._replace(in_loop=True)

    def with_break(self, has_break):
        return self._replace(has_break=has_break)

    def create_inner(self):
        return StaticLocalContext(
            global_context=self.global_context,
            outer_context=self,
            locally_defined_variables=(),
            locally_allocated_variables=frozenset(),
            locally_initialized_variables=frozenset(),
            last_output_flushed=self.last_output_flushed,
            index_variables=self.index_variables,
            in_loop=self.in_loop,
            has_break=False,
        )


class GlobalContext:
    __slots__ = ["interface", "variables", "bindings"]

    def __init__(self, interface):
        self.interface = interface
        self.variables = interface.global_variables
        self.bindings = BindingStorage(local_variables=interface.global_variables, parent=None)


class ProcedureContext:
    __slots__ = []

    def child(self, local_variables):
        return LocalContext(
            procedure=self,
            outer=self.global_context,
            local_variables=local_variables,
        )


class MainContext(ProcedureContext, namedtuple("MainContext", ["global_context"])):
    __slots__ = []


class CallbackContext(ProcedureContext, namedtuple("CallbackContext", [
    "global_context",
    "accept_context",
])):
    __slots__ = []


class LocalContext:
    __slots__ = [
        "procedure",
        "outer",
        "local_variables",
        "bindings",
    ]

    def __init__(self, *, procedure, outer, local_variables):
        if outer is None:
            parent = procedure.global_context.bindings
        else:
            parent = outer.bindings
        self.local_variables = local_variables
        self.bindings = BindingStorage(local_variables=local_variables, parent=parent)
        self.procedure = procedure
        self.outer = outer

    @property
    def variables(self):
        return dict(self.outer.variables, **self.local_variables)

    def child(self, local_variables):
        return LocalContext(
            procedure=self.procedure,
            outer=self,
            local_variables=local_variables,
        )


class FunctionCallContext:
    __slots__ = ["local_context", "accepted_callbacks"]

    def __init__(self, local_context):
        self.local_context = local_context
        self.accepted_callbacks = None


class AcceptCallbackContext:
    __slots__ = ["call_context", "callback"]

    def __init__(self, call_context):
        self.call_context = call_context
        self.callback = None
