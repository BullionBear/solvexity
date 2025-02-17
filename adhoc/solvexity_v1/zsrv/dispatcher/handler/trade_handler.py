from solvexity.trader.config import ConfigLoader
import zsrv.dispatcher.command as command
from zsrv.dispatcher.const import ERROR, TRADE_METHOD

class TradeHandler(command.CommandHandler):
    def __init__(self, config_loader: ConfigLoader):
        super().__init__()
    def execute(self, cmd: command.Command) -> command.Command:
        if cmd.command not in TRADE_METHOD.__dict__.values():
            return command.Command(ERROR.CMD_NOT_FOUND, message="Command not found")
        
        if cmd.command == TRADE_METHOD.HEALTH_CHECK:
            return self._health_check(cmd)
        return command.Command(ERROR.CMD_NOT_IMPLEMENTED, message="Command not implemented")
    
    def _health_check(self, cmd: command.Command) -> command.Command:
        return command.Command(TRADE_METHOD.HEALTH_CHECK, status="OK")