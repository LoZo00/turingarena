import threading
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from turingarena.pipeboundary import PipeBoundarySide, PipeBoundary
from turingarena.protocol.driver.client import DriverClient
from turingarena.sandbox.client import SandboxClient
from turingarena.sandbox.connection import SandboxConnection, SANDBOX_CHANNEL
from turingarena.sandbox.server import SandboxServer


class ProxiedAlgorithm:
    def __init__(self, *, algorithm_dir, interface):
        self.algorithm_dir = algorithm_dir
        self.interface = interface

    @contextmanager
    def run(self, **global_variables):
        with TemporaryDirectory("sandbox_server_") as server_dir:
            boundary = PipeBoundary(server_dir)
            boundary.create_channel(SANDBOX_CHANNEL)

            def server_target():
                with boundary.open_channel(SANDBOX_CHANNEL, PipeBoundarySide.SERVER) as pipes:
                    server = SandboxServer(SandboxConnection(**pipes))
                    server.run()

            server_thread = threading.Thread(target=server_target)
            server_thread.start()

            with boundary.open_channel(SANDBOX_CHANNEL, PipeBoundarySide.CLIENT) as pipes:
                client = SandboxClient(SandboxConnection(**pipes))

                with client.run(self.algorithm_dir) as process:
                    with DriverClient().run(interface=self.interface, process=process) as engine:
                        engine.begin_main(**global_variables)
                        proxy = Proxy(engine=engine)
                        yield process, proxy
                        engine.end_main()
            server_thread.join()


class Proxy:
    def __init__(self, engine):
        self._engine = engine

    def __getattr__(self, item):
        try:
            self._engine.interface_signature.functions[item]
        except KeyError:
            raise AttributeError

        def method(*args, **kwargs):
            return self._engine.call(item, args=args, callbacks_impl=kwargs)

        return method
