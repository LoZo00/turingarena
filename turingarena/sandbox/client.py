import logging
from contextlib import contextmanager

from turingarena.pipeboundary import PipeBoundarySide, PipeBoundary
from turingarena.sandbox.connection import SandboxProcessConnection, \
    SANDBOX_PROCESS_CHANNEL, SANDBOX_QUEUE, SANDBOX_REQUEST_QUEUE
from turingarena_impl.sandbox.processinfo import SandboxProcessInfo

logger = logging.getLogger(__name__)


class SandboxException(Exception):
    pass


class SandboxClient:
    def __init__(self, sandbox_dir):
        self.boundary = PipeBoundary(sandbox_dir)

    @contextmanager
    def run(self, *, language_name, source_name, interface_name):
        response = self.boundary.send_request(
            SANDBOX_QUEUE,
            language_name=language_name,
            source_name=source_name,
            interface_name=interface_name,
        )
        yield response["sandbox_process_dir"]


class SandboxProcessClient:
    def __init__(self, directory):
        self.boundary = PipeBoundary(directory)

    def get_info(self, *, wait=False):
        response = self.boundary.send_request(
            SANDBOX_REQUEST_QUEUE,
            wait=str(int(bool(wait))),
        )
        info = SandboxProcessInfo.from_payloads(response)
        logger.info(f"Process info: {info}")
        return info

    @contextmanager
    def connect(self):
        logger.debug("connecting to process...")
        with self.boundary.open_channel(SANDBOX_PROCESS_CHANNEL, PipeBoundarySide.CLIENT) as pipes:
            yield SandboxProcessConnection(**pipes)
