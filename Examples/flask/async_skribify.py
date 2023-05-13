import asyncio
from Skribify import Skribify

class AsyncSkribify(Skribify):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = asyncio.get_event_loop()

    async def __aenter__(self):
        await self.loop.run_in_executor(None, self.setup)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.teardown()

    async def setup(self):
        await self.loop.run_in_executor(None, super().setup)

    async def teardown(self):
        pass  