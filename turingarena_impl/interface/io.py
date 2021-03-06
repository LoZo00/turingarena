import logging
from collections import namedtuple
from contextlib import contextmanager

from turingarena_impl.interface.exceptions import CommunicationBroken, Diagnostic
from turingarena_impl.interface.executable import Instruction, ImperativeStatement
from turingarena_impl.interface.expressions import Expression

logger = logging.getLogger(__name__)


def read_line(pipe):
    line = pipe.readline()
    if not line:
        raise CommunicationBroken
    return line


@contextmanager
def writing_to_process():
    try:
        yield
    except BrokenPipeError:
        raise CommunicationBroken


def do_flush(connection):
    with writing_to_process():
        connection.downward.flush()


class CheckpointStatement(ImperativeStatement):
    __slots__ = []

    def generate_instructions(self, context):
        yield CheckpointInstruction()

    @property
    def context_after(self):
        return self.context.with_flushed_output(False)


class CheckpointInstruction(Instruction):
    __slots__ = []

    def should_send_input(self):
        return True

    def on_communicate_with_process(self, connection):
        do_flush(connection)

        line = read_line(connection.upward).strip()
        assert line == str(0)


class ReadWriteStatement(ImperativeStatement):
    __slots__ = []

    @property
    def arguments(self):
        return [
            Expression.compile(arg, self.context)
            for arg in self.ast.arguments
        ]

    def validate(self):
        for exp in self.arguments:
            yield from exp.validate()


class ReadWriteInstruction(Instruction, namedtuple("ReadWriteInstruction", [
    "arguments", "context"
])):
    __slots__ = []


class ReadStatement(ReadWriteStatement):
    __slots__ = []

    def generate_instructions(self, context):
        yield ReadInstruction(arguments=self.arguments, context=context)

    @property
    def context_after(self):
        return self.context.with_initialized_variables({
            exp.variable
            for exp in self.arguments
        })

    def validate(self):
        if not self.context.has_flushed_output:
            yield Diagnostic(Diagnostic.Messages.MISSING_FLUSH, parseinfo=self.ast.parseinfo)
        for exp in self.arguments:
            yield from exp.validate(lvalue=True)


class ReadInstruction(ReadWriteInstruction):
    def on_communicate_with_process(self, connection):
        raw_values = [
            a.evaluate_in(self.context).get()
            for a in self.arguments
        ]
        with writing_to_process():
            print(*raw_values, file=connection.downward)


class WriteStatement(ReadWriteStatement):
    __slots__ = []

    def generate_instructions(self, context):
        yield WriteInstruction(arguments=self.arguments, context=context)

    @property
    def context_after(self):
        return self.context.with_flushed_output(False)


class WriteInstruction(ReadWriteInstruction):
    __slots__ = []

    def on_communicate_with_process(self, connection):
        # make sure all input was sent before receiving output
        do_flush(connection)

        raw_values = read_line(connection.upward).strip().split()
        for a, v in zip(self.arguments, raw_values):
            value = int(v)
            a.evaluate_in(self.context).resolve(value)


class FlushStatement(ImperativeStatement):
    __slots__ = []

    def generate_instructions(self, context):
        yield FlushInstruction()

    @property
    def context_after(self):
        return self.context.with_flushed_output(True)


class FlushInstruction(Instruction):
    __slots__ = []

    def is_flush(self):
        return True
