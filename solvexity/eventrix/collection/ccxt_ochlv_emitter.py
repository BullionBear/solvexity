import logging

import ccxt.pro
from ccxt.pro import Exchange
from hooklet.base import BasePilot
from hooklet.eventrix.emitter import Emitter
from hooklet.types import GeneratorFunc

logger = logging.getLogger(__name__)


class CCXTOCHLVEmitter(Emitter):
    """
    CCXTOCHLVEmitter is a class that extends the Emitter class to emit OHLCV data
    from CCXT exchanges. It uses the ccxt.pro library to fetch real-time OHLCV data
    from the specified exchange and symbol.
    """

    def __init__(
        self,
        pilot: BasePilot,
        exchange_name: str,
        symbol: str,
        timeframe: str = "1m",
        default_type: str = "spot",
        subject: str | None = None,
        executor_id: str | None = None,
    ):
        super().__init__(pilot, executor_id)
        self.exchange_name = exchange_name
        self.client: Exchange = getattr(ccxt.pro, exchange_name)(
            {"options": {"defaultType": default_type}}
        )

        self.symbol = symbol
        self.timeframe = timeframe

        self.subject = (
            f"{self.exchange_name}:{self.symbol}:{self.timeframe}"
            if subject is None
            else subject
        )
        self.client: Exchange = getattr(ccxt.pro, exchange_name)(
            {
                "options": {"defaultType": default_type},
            }
        )

        self.symbol = symbol
        self.timeframe = timeframe

        self.subject = (
            f"{self.exchange_name}:{self.symbol}:{self.timeframe}"
            if subject is None
            else subject
        )
        self.default_type = default_type

    async def on_start(self) -> None:
        await self.client.load_markets()
        await super().on_start()

    async def on_finish(self) -> None:
        await super().on_stop()
        await self.client.close()

    async def get_generators(self) -> dict[str, GeneratorFunc]:
        """
        Get the generator function for emitting OHLCV data.

        :return: A dictionary with the generator function for emitting OHLCV data.
        """

        return {
            self.subject: self._ohlcv_generator,  # Pass the function, not the generator object
        }

    async def _ohlcv_generator(self):
        while self.is_running():
            try:
                ochlvs = await self.client.watch_ohlcv(self.symbol, self.timeframe)
                logging.info(f"Received OHLCV data: {ochlvs}")
                for ochlv in ochlvs:
                    # Emit the OHLCV data
                    yield {"ochlv": ochlv}
            except Exception as e:
                logging.error(
                    f"Error in CCXTOCHLVEmitter: {type(e).__name__} - {str(e)}"
                )
            finally:
                await self.client.close()
                self.client = getattr(ccxt.pro, self.exchange_name)(
                    {"options": {"defaultType": self.default_type}}
                )
                await self.client.load_markets()
