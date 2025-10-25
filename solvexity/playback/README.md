# Playback Module

The playback module provides tools for filtering, replaying, and verifying protobuf Trade messages from raw binary files.

## Overview

This module contains:
- **replay.py**: Replays and summarizes trade messages from `.raw` files
- **tag.py**: Generates metadata and validates trade data integrity
- **serde/**: Serialization and deserialization utilities

## Basic Usage

### Filter by Symbol

Filter trade messages by symbol (e.g., BTC) using the `marshal` binary tool:

```bash
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | marshal -s -o message-btc.raw
```

This command:
1. Reads `message-example.raw` (protobuf Trade messages)
2. Deserializes to JSON (`marshal -d`)
3. Filters for BTC trades using `jq`
4. Serializes back to protobuf (`marshal -s`)
5. Outputs to `message-btc.raw`

### Filter by Exchange

Filter trades from a specific exchange (exchange values: 1=BINANCE, 2=BINANCE_PERP, 3=BYBIT):

```bash
# Binance spot trades
cat message-example.raw | marshal -d | jq -c 'select(.exchange == 1)' | marshal -s -o message-binance.raw

# Binance perpetual futures
cat message-example.raw | marshal -d | jq -c 'select(.exchange == 2)' | marshal -s -o message-binance-perp.raw

# Bybit trades
cat message-example.raw | marshal -d | jq -c 'select(.exchange == 3)' | marshal -s -o message-bybit.raw
```

### Filter by Instrument Type

Filter by instrument type (instrument values: 1=SPOT, 2=MARGIN, 3=PERP, 4=INVERSE, 5=FUTURES, 6=OPTION):

```bash
# Perpetual futures trades
cat message-example.raw | marshal -d | jq -c 'select(.instrument == 3)' | marshal -s -o message-perp.raw

# Spot trades
cat message-example.raw | marshal -d | jq -c 'select(.instrument == 1)' | marshal -s -o message-spot.raw
```

### Filter by Side (Buy/Sell)

Filter by trade side (side values: 1=BUY, 2=SELL):

```bash
# Buy orders only
cat message-example.raw | marshal -d | jq -c 'select(.side == 1)' | marshal -s -o message-buy.raw

# Sell orders only
cat message-example.raw | marshal -d | jq -c 'select(.side == 2)' | marshal -s -o message-sell.raw
```

## Query by ID Range

Extract trades within a specific ID range:

```bash
# Trades with ID between 1000 and 2000
cat message-example.raw | marshal -d | jq -c 'select(.id >= 1000 and .id <= 2000)' | marshal -s -o message-id-1000-2000.raw
```

Combine ID range with symbol filter:

```bash
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC" and .id >= 1000 and .id <= 2000)' | marshal -s -o message-btc-id-1000-2000.raw
```

## Query by Timestamp Range

Filter trades within a time range:

```bash
# Trades within a specific timestamp range (Unix timestamp in milliseconds)
cat message-example.raw | marshal -d | jq -c 'select(.timestamp >= 1640995200000 and .timestamp <= 1641081600000)' | marshal -s -o message-timestamp-range.raw
```

## Complex Filters

### Multiple Conditions

Combine multiple conditions by chaining multiple `jq` filters:

```bash
# BTC spot trades on Binance (exchange=1, instrument=1)
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | jq -c 'select(.instrument == 1)' | jq -c 'select(.exchange == 1)' | marshal -s -o message-btc-spot-binance.raw
```

This approach is recommended over combining all conditions in a single `jq` statement for better readability and performance.

### Price Range Filter

Filter by price range:

```bash
# Trades above a certain price
cat message-example.raw | marshal -d | jq -c 'select(.price > 50000)' | marshal -s -o message-high-price.raw
```

### Volume Filter

Filter by quantity/volume:

```bash
# Large trades (above 1.0)
cat message-example.raw | marshal -d | jq -c 'select(.quantity > 1.0)' | marshal -s -o message-large-volume.raw
```

## Verification and Metadata

### Generate Metadata

Generate metadata for a `.raw` file using the `tag.py` script:

```bash
python -m solvexity.playback.tag -i message-btc.raw -o message-btc-metadata.json
```

This creates a JSON metadata file containing:
- File path and MD5 checksum
- Segments grouped by exchange, instrument, and symbol
- For each segment:
  - Start and end ID
  - Start and end timestamp
  - Total volume and quote volume
  - Total number of trades

### Verify Filtered Data

After filtering, verify the result:

```bash
# Generate metadata for the filtered file
python -m solvexity.playback.tag -i message-btc.raw -o message-btc-metadata.json

# View the metadata
cat message-btc-metadata.json | jq '.'
```

### Post-Verification Example

The `tag.py` script supports post-verification queries on the generated metadata:

```bash
# First, generate metadata
python -m solvexity.playback.tag -i message-example.raw -o metadata.json

# Then query the metadata to verify
cat metadata.json | jq '.segments[] | select(.start_id >= 1000 and .end_id <= 2000)'
```

This allows you to verify which segments of data match your query criteria before performing the actual filtering.

## Replay and Summary

View a summary of trade messages in a `.raw` file:

```bash
python -m solvexity.playback.replay -i message-example.raw
```

This displays:
- Exchange, instrument, and symbol information
- ID ranges (start_id and current_id)
- Time ranges (open_time and close_time)
- Total volume and quote volume
- Total number of trades

## File Format

The `.raw` files contain protobuf Trade messages with the following structure:

```protobuf
message Trade {
  int64 id = 1;
  app.Exchange exchange = 2;
  app.Instrument instrument = 3;
  app.Symbol symbol = 4;
  app.Side side = 5;
  double price = 7;
  double quantity = 8;
  int64 timestamp = 9;
}
```

Where:
- `id`: Unique trade identifier
- `exchange`: Exchange enum (numeric value)
- `instrument`: Instrument type (numeric value)
- `symbol`: Trading pair with `base` and `quote` fields (strings)
- `side`: Trade side (numeric value)
- `price`: Trade price
- `quantity`: Trade quantity
- `timestamp`: Unix timestamp in milliseconds

### Enum Values Reference

**Exchange Values:**
- `0`: EXCHANGE_UNSPECIFIED
- `1`: EXCHANGE_BINANCE
- `2`: EXCHANGE_BINANCE_PERP
- `3`: EXCHANGE_BYBIT

**Instrument Values:**
- `0`: INSTRUMENT_UNSPECIFIED
- `1`: INSTRUMENT_SPOT
- `2`: INSTRUMENT_MARGIN
- `3`: INSTRUMENT_PERP
- `4`: INSTRUMENT_INVERSE
- `5`: INSTRUMENT_FUTURES
- `6`: INSTRUMENT_OPTION

**Side Values:**
- `0`: SIDE_UNSPECIFIED
- `1`: SIDE_BUY
- `2`: SIDE_SELL

## Advanced Usage

### Chain Multiple Filters

```bash
# Filter BTC trades, then filter by timestamp
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | marshal -s -o message-btc.raw
cat message-btc.raw | marshal -d | jq -c 'select(.timestamp >= 1640995200000)' | marshal -s -o message-btc-filtered.raw
```

### Count Messages

Count filtered messages:

```bash
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | wc -l
```

### Inspect Sample Messages

Preview filtered messages:

```bash
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | head -5
```

### Pretty Print

Format JSON output for readability:

```bash
cat message-example.raw | marshal -d | jq 'select(.symbol.base == "BTC")' | head -5
```

## Common Workflows

### 1. Extract and Verify BTC Trades

```bash
# Filter
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | marshal -s -o message-btc.raw

# Generate metadata
python -m solvexity.playback.tag -i message-btc.raw -o message-btc-metadata.json

# Review summary
python -m solvexity.playback.replay -i message-btc.raw
```

### 2. Extract ID Range and Verify

```bash
# Filter by ID range
cat message-example.raw | marshal -d | jq -c 'select(.id >= 1000 and .id <= 2000)' | marshal -s -o message-range.raw

# Verify integrity
python -m solvexity.playback.tag -i message-range.raw -o message-range-metadata.json

# Check metadata to confirm ID ranges
cat message-range-metadata.json | jq '.segments[] | {start_id, end_id}'
```

### 3. Multi-Criteria Filter

```bash
# Filter: BTC perpetual futures trades on Binance with buy side (exchange=1, instrument=3, side=1)
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | jq -c 'select(.instrument == 3)' | jq -c 'select(.exchange == 1)' | jq -c 'select(.side == 1)' | marshal -s -o message-btc-perp-binance-buy.raw

# Verify
python -m solvexity.playback.tag -i message-btc-perp-binance-buy.raw -o metadata.json
python -m solvexity.playback.replay -i message-btc-perp-binance-buy.raw
```

## Best Practices

### Chaining Multiple jq Filters

When filtering with multiple conditions, prefer chaining multiple `jq` filters instead of combining them into a single `select()` statement:

**Recommended:**
```bash
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC")' | jq -c 'select(.exchange == 1)' | marshal -s -o output.raw
```

**Not Recommended:**
```bash
cat message-example.raw | marshal -d | jq -c 'select(.symbol.base == "BTC" and .exchange == 1)' | marshal -s -o output.raw
```

Benefits of chaining:
- Better readability - each filter is a distinct step
- Easier to debug - you can inspect intermediate results
- Better performance - filters are applied sequentially, reducing the data at each stage
- More maintainable - easy to add or remove conditions

## Notes

- The `marshal` binary tool must be available in your PATH
- Ensure `jq` is installed for JSON filtering
- The Python scripts require the solvexity package to be installed
- All timestamps are in Unix milliseconds
- ID ranges should be consecutive for proper segmentation
