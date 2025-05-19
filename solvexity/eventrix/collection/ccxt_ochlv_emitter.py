import logging
import asyncio
import ccxt.pro
from solvexity.eventrix.config import ConfigType
from typing import Any
from ccxt.pro import Exchange
from hooklet.base import BasePilot
from hooklet.eventrix.emitter import Emitter
from hooklet.types import GeneratorFunc

logger = logging.getLogger(__name__)

class CCTXOCHLVConfig(ConfigType):
    exchange_name: str
    symbol: str
    timeframe: str = "1m"
    default_type: str = "spot"
    subject: str | None = None
    executor_id: str | None = None


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
        self.default_type = default_type


    async def on_start(self) -> None:
        await self.client.load_markets()
        await super().on_start()

    @property
    def status(self) -> dict[str, Any]:
        base_status = super().status
        curr_status = {
            "exchange_name": self.exchange_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "default_type": self.default_type,
        }
        return {**base_status, **curr_status}


    async def on_finish(self) -> None:
        """
        Clean up resources when the emitter is finished.
        """
        try:
            # Close the CCXT connection explicitly as required
            if hasattr(self, 'client') and self.client:
                await self.client.close()
                logger.info(f"Closed CCXT connection for {self.exchange_name}")
        except Exception as e:
            logger.error(f"Error closing CCXT client: {type(e).__name__} - {str(e)}")
        finally:
            # Call parent's on_finish to clean up other resources
            await super().on_finish()

    async def on_stop(self) -> None:
        """
        Handle cleanup when the emitter is stopped.
        """
        try:
            if hasattr(self, 'client') and self.client:
                await self.client.close()
                logger.info(f"Closed CCXT connection on stop for {self.exchange_name}")
        except Exception as e:
            logger.error(f"Error closing CCXT client on stop: {type(e).__name__} - {str(e)}")
        finally:
            await super().on_stop()

    async def get_generators(self) -> dict[str, GeneratorFunc]:
        """
        Get the generator function for emitting OHLCV data.

        :return: A dictionary with the generator function for emitting OHLCV data.
        """
        return {
            self.subject: self._ohlcv_generator,  # Pass the function, not the generator object
        }

    async def _ohlcv_generator(self):
        """
        Generator function that emits OHLCV data.
        """
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
                # Brief pause to prevent tight error loop
                await asyncio.sleep(1)
                
                # If client is in a bad state, try to reconnect
                try:
                    if hasattr(self, 'client') and self.client:
                        await self.client.close()
                    self.client = getattr(ccxt.pro, self.exchange_name)(
                        {"options": {"defaultType": self.default_type}}
                    )
                    await self.client.load_markets()
                except Exception as reconnect_error:
                    logging.error(f"Failed to reconnect: {type(reconnect_error).__name__} - {str(reconnect_error)}")
                    await asyncio.sleep(5)  # Longer pause after reconnect failure
