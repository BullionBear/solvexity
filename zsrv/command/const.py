class GENERAL_METHOD:
    HEALTH_CHECK = 'health_check'
    SYSTEM_CONFIG = 'system_config'
    SERVICE_CONFIG = 'service_config'
    LATEST_FEED = 'latest_feed'

class TRADE_METHOD(GENERAL_METHOD):
    SPOT_BALANCE = 'spot_balance'

class FEED_METHOD(GENERAL_METHOD):
    LIST_CHANNEL = 'list_channel'

class ALL_METHOD(TRADE_METHOD, FEED_METHOD):
    pass


class ERROR:
    CMD_NOT_FOUND = 'command_not_found'
    CMD_INVALID_INPUT = 'command_invalid_input'