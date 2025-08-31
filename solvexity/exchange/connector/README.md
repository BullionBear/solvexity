# Exchange Connectivity SDK

A lightweight, robust Python SDK for connecting to cryptocurrency exchange APIs (REST & WebSocket). This library handles the complex low-level networking so you can focus on building your trading logic.

## Features

- Pythonic REST Interface: High-level, well-typed methods for common API endpoints (e.g., get_ohlcv(), get_ticker()).

- Unified WebSocket Interface: Consistent, easy-to-use patterns for real-time data streams.

- Robust Connection Management: Automatically handles WebSocket ping/pong, reconnection, and error recovery.

- Protocol Separation: Cleanly organized clients for REST, public WebSocket streams, and private WebSocket feeds.

- Minimalist Data Handling: Provides raw data structures for WebSocket events and complex responses for flexibility.

- Callback Flexibility: Accepts both async and synchronous functions for handling real-time events.

