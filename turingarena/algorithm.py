import logging
import os
from collections import namedtuple
from contextlib import contextmanager, ExitStack

from turingarena import AlgorithmRuntimeError, TimeLimitExceeded, MemoryLimitExceeded, InterfaceExit
from turingarena.driver.client import SandboxError

logger = logging.getLogger(__name__)


class Algorithm(namedtuple("Algorithm", [
    "source_name", "language_name", "interface_name",
])):
    @contextmanager
    def run(self, global_variables=None, time_limit=None):
        # FIXME: make imports global
        from turingarena.driver.client import DriverClient, DriverProcessClient
        from turingarena.sandbox.client import SandboxClient, SandboxProcessClient

        if global_variables is None:
            global_variables = {}

        with ExitStack() as stack:
            sandbox_dir = os.environ["TURINGARENA_SANDBOX_DIR"]

            sandbox_client = SandboxClient(sandbox_dir)
            sandbox_process_dir = stack.enter_context(sandbox_client.run(
                source_name=self.source_name,
                language_name=self.language_name,
                interface_name=self.interface_name,
            ))

            sandbox_process_client = SandboxProcessClient(sandbox_process_dir)

            driver_dir = os.environ["TURINGARENA_DRIVER_DIR"]

            driver_client = DriverClient(driver_dir)
            driver_process_dir = stack.enter_context(
                driver_client.run_driver(
                    interface_name=self.interface_name,
                    sandbox_process_dir=sandbox_process_dir,
                )
            )

            driver_process_client = DriverProcessClient(driver_process_dir)

            algorithm_process = AlgorithmProcess(
                sandbox=sandbox_process_client,
                driver=driver_process_client,
            )

            try:
                with algorithm_process.run(algorithm_process.sandbox, time_limit):
                    driver_process_client.send_begin_main(global_variables)
                    try:
                        yield algorithm_process
                    except InterfaceExit:
                        driver_process_client.send_exit()
                    else:
                        driver_process_client.send_end_main()
            except SandboxError:
                info = sandbox_process_client.get_info(wait=True)
                if info.error:
                    raise AlgorithmRuntimeError(info.error) from None
                raise
            sandbox_process_client.get_info(wait=True)


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

    def exit(self):
        raise InterfaceExit
