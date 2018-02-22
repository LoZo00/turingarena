import logging
import os
import sys
import tempfile
from contextlib import ExitStack
from threading import Thread

from turingarena.sandbox.client import ProcessConnection
from turingarena.sandbox.exceptions import AlgorithmRuntimeError
from turingarena.sandbox.executables import load_executable

logger = logging.getLogger(__name__)


class SandboxException(Exception):
    pass


class SandboxProcess:
    def __init__(self, *, sandbox_dir, executable):
        self.executable = executable
        self.sandbox_dir = sandbox_dir

        self.downward_pipe_name = os.path.join(sandbox_dir, "downward.pipe")
        self.upward_pipe_name = os.path.join(sandbox_dir, "upward.pipe")
        self.error_pipe_name = os.path.join(sandbox_dir, "error.pipe")
        self.wait_pipe_name = os.path.join(sandbox_dir, "wait.pipe")

        self.os_process = None

        logger.debug("sandbox folder: %s", sandbox_dir)

        logger.debug("creating pipes...")
        os.mkfifo(self.downward_pipe_name)
        os.mkfifo(self.upward_pipe_name)
        os.mkfifo(self.error_pipe_name)
        os.mkfifo(self.wait_pipe_name)
        logger.debug("pipes created")

        print(self.sandbox_dir)
        sys.stdout.close()

        wait_thread = None
        try:
            with ExitStack() as stack:
                logger.debug("opening downward pipe...")
                downward_pipe = stack.enter_context(open(self.downward_pipe_name, "r"))
                logger.debug("opening upward pipe...")
                upward_pipe = stack.enter_context(open(self.upward_pipe_name, "w"))
                logger.debug("opening error pipe...")
                error_pipe = stack.enter_context(open(self.error_pipe_name, "w"))
                logger.debug("pipes opened")

                connection = ProcessConnection(
                    downward_pipe=downward_pipe,
                    upward_pipe=upward_pipe,
                    error_pipe=error_pipe,
                )

                try:
                    with self.executable.run(connection) as p:
                        def wait():
                            logger.debug("opening wait pipe...")
                            with open(self.wait_pipe_name, "w"):
                                pass
                            logger.debug("wait pipe opened, terminating...")
                            p.kill()

                        wait_thread = Thread(target=wait)
                        wait_thread.start()
                except AlgorithmRuntimeError as e:
                    logger.exception(e)
                    error_pipe.write(str(e))
        finally:
            if wait_thread:
                wait_thread.join()


def sandbox_run(algorithm_dir):
    prefix = "turingarena_sandbox_"

    executable = load_executable(algorithm_dir)
    with tempfile.TemporaryDirectory(prefix=prefix) as sandbox_dir:
        SandboxProcess(executable=executable, sandbox_dir=sandbox_dir)
