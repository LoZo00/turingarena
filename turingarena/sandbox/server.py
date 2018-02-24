import logging
import tempfile
import threading
from threading import Thread

from turingarena.pipeboundary import PipeBoundarySide, PipeBoundary
from turingarena.sandbox.connection import SandboxProcessConnection, SANDBOX_PROCESS_CHANNEL, \
    SANDBOX_WAIT_BARRIER
from turingarena.sandbox.exceptions import AlgorithmRuntimeError
from turingarena.sandbox.executables import load_executable

logger = logging.getLogger(__name__)


class SandboxException(Exception):
    pass


class SandboxServer:
    def __init__(self, connection):
        self.connection = connection

    def serve_one(self, executable, response_sent):
        with tempfile.TemporaryDirectory(
                prefix="turingarena_sandbox_process_",
        ) as sandbox_dir:
            process_server = SandboxProcessServer(executable=executable, sandbox_dir=sandbox_dir)
            print(sandbox_dir, file=self.connection.response, flush=True)
            response_sent.set()
            process_server.run()

    def run(self):
        response_sent = threading.Event()
        while True:
            line = self.connection.request.readline()
            if not line: break
            algorithm_dir, = line.splitlines()
            executable = load_executable(algorithm_dir)
            threading.Thread(target=lambda: self.serve_one(executable, response_sent)).start()
            response_sent.wait()


class SandboxProcessServer:
    def __init__(self, *, sandbox_dir, executable):
        self.executable = executable

        logger.debug("sandbox folder: %s", sandbox_dir)

        self.boundary = PipeBoundary(sandbox_dir)
        self.boundary.create_channel(SANDBOX_PROCESS_CHANNEL)
        self.boundary.create_channel(SANDBOX_WAIT_BARRIER)

    def run(self):
        wait_thread = None
        with self.boundary.open_channel(SANDBOX_PROCESS_CHANNEL, PipeBoundarySide.SERVER) as pipes:
            connection = SandboxProcessConnection(**pipes)
            try:
                with self.executable.run(connection):
                    wait_thread = Thread(target=self.wait_for_wait_pipe)
                    wait_thread.start()
            except AlgorithmRuntimeError as e:
                logger.exception(e)
                # FIXME: connection.error_pipe.write(str(e))
        if wait_thread:
            wait_thread.join()

    def wait_for_wait_pipe(self):
        with self.boundary.open_channel(SANDBOX_WAIT_BARRIER, PipeBoundarySide.SERVER):
            pass
        logger.debug("wait barrier reached, terminating...")
