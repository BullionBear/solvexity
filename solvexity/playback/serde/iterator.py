from typing import Iterator
from solvexity.model import Trade, Exchange, Instrument, Side
from typing import Optional, Tuple

class TradeIterator:
    """Replays protobuf Trade messages from binary data."""

    def replay_from_files(self, filenames: list[str]) -> Iterator[Trade]:
        """
        Replay trade messages from a binary file.
        
        Args:
            filenames: List of paths to the binary files containing serialized messages
            
        Returns:
            Iterator of Trade objects
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            IOError: If there's an error reading the file
        """
        try:
            for filename in filenames:
                with open(filename, 'rb') as f:
                    # Read entire file for better performance on small files
                    data = f.read()
                    accumulated = bytearray(data)
                    data_view = memoryview(accumulated)
                    offset = 0
                    data_len = len(accumulated)

                    while offset < data_len - 10:  # Minimum viable message size
                        # Parse next message and get the Trade object directly
                        trade, consumed, found = self._parse_next_message_fast(data_view[offset:])
                        if trade is not None:
                            yield trade

                        if not found:
                            # Skip one byte and try again
                            offset += 1
                            continue
                        offset += consumed
        except FileNotFoundError:
            raise FileNotFoundError(f"Failed to open file: {filename}")
        except IOError as e:
            raise IOError(f"Error reading file: {e}")

        return

    def _parse_next_message_fast(self, data: memoryview) -> Tuple[Optional[Trade], int, bool]:
        """
        Parse the next complete protobuf message from the data (optimized version).
        
        Returns the parsed Trade object directly using pydantic model.
        
        Args:
            data: Memoryview containing potential protobuf messages
            
        Returns:
            Tuple of (trade_object, consumed_bytes, found)
        """
        data_len = len(data)
        if data_len < 10:
            return None, 0, False

        offset = 0
        fields_seen = 0  # Use bitmask instead of dict for faster lookup
        field_map = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 7: 32, 8: 64, 9: 128}
        expected_mask = 255  # All 8 fields = 1+2+4+8+16+32+64+128

        # Reasonable upper bound for a single message
        max_offset = min(data_len, 200)

        while offset < max_offset:
            if offset + 1 >= data_len:
                break

            # Read field header (field number + wire type)
            field_header = data[offset]
            field_num = field_header >> 3
            wire_type = field_header & 0x7
            offset += 1

            # Skip invalid field numbers (protobuf fields start at 1)
            if field_num == 0 or field_num > 20:
                break

            # Skip the field data based on wire type (inlined for performance)
            if wire_type == 0:  # Varint
                field_length = self._skip_varint_fast(data, offset, data_len)
                if field_length == 0:
                    break
            elif wire_type == 1:  # 64-bit fixed
                if offset + 8 > data_len:
                    break
                field_length = 8
            elif wire_type == 2:  # Length-delimited
                field_length = self._skip_length_delimited_fast(data, offset, data_len)
                if field_length == 0:
                    break
            elif wire_type == 5:  # 32-bit fixed
                if offset + 4 > data_len:
                    break
                field_length = 4
            else:
                break  # Unknown wire type

            offset += field_length
            
            # Mark field as seen using bitmask
            if field_num in field_map:
                fields_seen |= field_map[field_num]

            # Check if we have all expected fields
            if fields_seen == expected_mask:
                # We've seen all expected fields, try to parse using pydantic model
                candidate = bytes(data[:offset])
                try:
                    trade = Trade.from_protobuf_bytes(candidate)
                    # Quick validation using pydantic model properties
                    if (trade.id > 0 and 
                        trade.exchange != Exchange.EXCHANGE_UNSPECIFIED and 
                        trade.instrument != Instrument.INSTRUMENT_UNSPECIFIED and
                        trade.side != Side.SIDE_UNSPECIFIED):
                        return trade, offset, True
                except Exception:  # Catch any parsing errors
                    pass

        return None, 0, False

    def _skip_varint_fast(self, data: memoryview, offset: int, data_len: int) -> int:
        """Fast varint skipping (inlined logic)."""
        max_bytes = min(offset + 10, data_len)
        for i in range(offset, max_bytes):
            if data[i] & 0x80 == 0:
                return i - offset + 1
        return 0

    def _skip_length_delimited_fast(self, data: memoryview, offset: int, data_len: int) -> int:
        """Fast length-delimited field skipping."""
        # Decode the length varint
        length = 0
        length_bytes = 0
        max_bytes = min(offset + 10, data_len)

        for i in range(offset, max_bytes):
            length |= (data[i] & 0x7F) << (7 * length_bytes)
            length_bytes += 1
            if data[i] & 0x80 == 0:
                break

        if length_bytes == 0:
            return 0

        # Check if we have enough data
        total_length = length_bytes + length
        if offset + total_length > data_len:
            return 0
        
        return total_length