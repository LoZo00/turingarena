import logging
import threading
from collections import namedtuple
from contextlib import contextmanager, ExitStack
from tempfile import TemporaryDirectory
from time import sleep

from turingarena.sandbox.exceptions import AlgorithmRuntimeError, TimeLimitExceeded, MemoryLimitExceeded

logger = logging.getLogger(__name__)


class Algorithm(namedtuple("Algorithm", [
    "source_name", "language_name", "interface_name",
])):
    @contextmanager
    def run(self, global_variables=None, time_limit=None):
        # FIXME: make imports global
        from turingarena.interface.driver.client import DriverClient, DriverProcessClient
        from turingarena.interface.driver.server import DriverServer
        from turingarena.sandbox.client import SandboxClient, SandboxProcessClient
        from turingarena.sandbox.server import SandboxServer

        if global_variables is None:
            global_variables = {}

        with ExitStack() as stack:
            sandbox_dir = stack.enter_context(
                TemporaryDirectory(dir="/tmp", prefix="sandbox_server_")
            )

            sandbox_server = SandboxServer(sandbox_dir)
            sandbox_client = SandboxClient(sandbox_dir)

            sandbox_server_thread = threading.Thread(target=sandbox_server.run)
            sandbox_server_thread.start()
            stack.callback(sandbox_server_thread.join)
            stack.callback(sandbox_server.stop)

            sandbox_process_dir = stack.enter_context(sandbox_client.run(
                source_name=self.source_name,
                language_name=self.language_name,
                interface_name=self.interface_name,
            ))
            driver_dir = stack.enter_context(
                TemporaryDirectory(dir="/tmp", prefix="driver_server_")
            )
            sandbox_process_client = SandboxProcessClient(sandbox_process_dir)

            driver_server = DriverServer(driver_dir)
            driver_client = DriverClient(driver_dir)

            driver_server_thread = threading.Thread(target=driver_server.run)
            driver_server_thread.start()
            stack.callback(driver_server_thread.join)
            stack.callback(driver_server.stop)

            driver_process_dir = stack.enter_context(
                driver_client.run_driver(
                    interface_name=self.interface_name,
                    sandbox_process_dir=sandbox_process_dir,
                )
            )

            driver_process_client = DriverProcessClient(driver_process_dir)

            try:
                algorithm_process = AlgorithmProcess(
                    sandbox=sandbox_process_client,
                    driver=driver_process_client,
                )
                # FIXME: not cool
                sleep(3)  # wait for sandbox to settle before measuring time
                with algorithm_process.run(algorithm_process.sandbox, time_limit):
                    driver_process_client.send_begin_main(global_variables)
                    yield algorithm_process
                    driver_process_client.send_end_main()
            finally:
                info = sandbox_process_client.wait()
                if info.error:
                    raise AlgorithmRuntimeError(info.error)


class AlgorithmSection:
    def __init__(self):
        self.info_before = None
        self.info_after = None

    def finished(self, info_before, info_after):
        self.info_before = info_before
        self.info_after = info_after

    @contextmanager
    def run(self, sandbox, time_limit):
        info_before = sandbox.get_info()
        yield self
        info_after = sandbox.get_info()
        self.finished(info_before, info_after)
        if time_limit is not None and self.time_usage > time_limit:
            raise TimeLimitExceeded(self.time_usage, time_limit)

    @property
    def time_usage(self):
        return self.info_after.time_usage - self.info_before.time_usage


class AlgorithmProcess(AlgorithmSection):
    def __init__(self, *, sandbox, driver):
        super().__init__()
        self.sandbox = sandbox
        self.driver = driver
        self.call = driver.proxy

    def section(self, *, time_limit=None):
        section_info = AlgorithmSection()
        return section_info.run(self.sandbox, time_limit=time_limit)

    def limit_memory(self, value):
        info = self.sandbox.get_info()
        if info.memory_usage > value:
            raise MemoryLimitExceeded(info.memory_usage, value)
