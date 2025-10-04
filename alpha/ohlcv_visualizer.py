#!/usr/bin/env python3
"""
OHLCV Data Visualization Script

This script reads OHLCV data from CSV files and creates candlestick charts
with volume and optional technical indicators.

Usage:
    python ohlcv_visualizer.py --input dataframe.csv --output chart.png
    python ohlcv_visualizer.py --input dataframe.csv --output chart.html --format html
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import os
import sys


class OHLCVVisualizer:
    """OHLCV Data Visualization Class"""
    
    def __init__(self):
        self.df = None
        self.fig = None
        self.axes = None
        
    def load_data(self, input_file):
        """Load OHLCV data from CSV file"""
        try:
            self.df = pd.read_csv(input_file)
            print(f"Loaded {len(self.df)} rows from {input_file}")
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
                
            # Create a simple index for x-axis (ignoring timestamps since bars are not equal intervals)
            self.df['bar_index'] = range(len(self.df))
            
            print(f"Data columns: {list(self.df.columns)}")
            print(f"Number of bars: {len(self.df)}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    
    def calculate_sma(self, period=20):
        """Calculate Simple Moving Average"""
        if self.df is None:
            return None
        return self.df['close'].rolling(window=period).mean()
    
    def calculate_ema(self, period=20):
        """Calculate Exponential Moving Average"""
        if self.df is None:
            return None
        return self.df['close'].ewm(span=period).mean()
    
    def create_candlestick_chart(self, show_volume=True, show_sma=True, show_ema=True):
        """Create candlestick chart with volume and indicators"""
        if self.df is None:
            print("No data loaded. Please load data first.")
            return
        
        # Create figure with subplots
        if show_volume:
            self.fig, (self.axes, vol_ax) = plt.subplots(2, 1, figsize=(15, 10), 
                                                        gridspec_kw={'height_ratios': [3, 1]})
        else:
            self.fig, self.axes = plt.subplots(1, 1, figsize=(15, 8))
            vol_ax = None
        
        # Use bar index for x-axis (since bars are not equal time intervals)
        bar_indices = self.df['bar_index']
        
        # Plot candlesticks
        self._plot_candlesticks(bar_indices)
        
        # Add moving averages
        if show_sma:
            sma_20 = self.calculate_sma(20)
            if sma_20 is not None:
                self.axes.plot(bar_indices, sma_20, label='SMA 20', color='blue', alpha=0.7, linewidth=1)
        
        if show_ema:
            ema_20 = self.calculate_ema(20)
            if ema_20 is not None:
                self.axes.plot(bar_indices, ema_20, label='EMA 20', color='orange', alpha=0.7, linewidth=1)
        
        # Format price chart
        self._format_price_chart()
        
        # Plot volume if requested
        if show_volume and vol_ax is not None:
            self._plot_volume(bar_indices, vol_ax)
        
        # Add title and labels
        symbol = self.df.get('symbol.base', ['Unknown']).iloc[0] if 'symbol.base' in self.df.columns else 'Unknown'
        quote = self.df.get('symbol.quote', ['Unknown']).iloc[0] if 'symbol.quote' in self.df.columns else 'Unknown'
        title = f"{symbol}/{quote} OHLCV Chart"
        
        self.axes.set_title(title, fontsize=16, fontweight='bold')
        
        # Only show legend if there are indicators to display
        if show_sma or show_ema:
            self.axes.legend()
        
        plt.tight_layout()
    
    def _plot_candlesticks(self, bar_indices):
        """Plot candlestick chart"""
        for i, (bar_index, open_price, high, low, close) in enumerate(zip(
            bar_indices, self.df['open'], self.df['high'], self.df['low'], self.df['close'])):
            
            # Determine color based on open vs close
            color = 'green' if close >= open_price else 'red'
            
            # Draw the wick (high-low line)
            self.axes.plot([bar_index, bar_index], [low, high], color='black', linewidth=0.5)
            
            # Draw the body (open-close rectangle)
            body_height = abs(close - open_price)
            body_bottom = min(open_price, close)
            
            # Create rectangle for the body
            rect = Rectangle((bar_index - 0.3, body_bottom), 0.6, body_height, 
                           facecolor=color, edgecolor='black', alpha=0.8)
            self.axes.add_patch(rect)
    
    def _format_price_chart(self):
        """Format the price chart"""
        # Format x-axis (using bar indices instead of dates)
        self.axes.set_xlabel('Bar Index', fontsize=12)
        
        # Format y-axis
        self.axes.set_ylabel('Price', fontsize=12)
        self.axes.grid(True, alpha=0.3)
        
        # Set y-axis limits with some padding
        price_min = self.df[['open', 'high', 'low', 'close']].min().min()
        price_max = self.df[['open', 'high', 'low', 'close']].max().max()
        price_range = price_max - price_min
        self.axes.set_ylim(price_min - price_range * 0.1, price_max + price_range * 0.1)
    
    def _plot_volume(self, bar_indices, vol_ax):
        """Plot volume bars"""
        # Color volume bars based on price movement
        colors = ['green' if close >= open_price else 'red' 
                 for close, open_price in zip(self.df['close'], self.df['open'])]
        
        vol_ax.bar(bar_indices, self.df['volume'], color=colors, alpha=0.6, width=0.8)
        vol_ax.set_ylabel('Volume', fontsize=12)
        vol_ax.set_xlabel('Bar Index', fontsize=12)
        vol_ax.grid(True, alpha=0.3)
    
    def save_chart(self, output_file, format_type='png'):
        """Save the chart to file"""
        if self.fig is None:
            print("No chart created. Please create chart first.")
            return
        
        try:
            if format_type.lower() == 'png':
                self.fig.savefig(output_file, dpi=300, bbox_inches='tight', 
                               facecolor='white', edgecolor='none')
            elif format_type.lower() == 'pdf':
                self.fig.savefig(output_file, bbox_inches='tight', 
                               facecolor='white', edgecolor='none')
            elif format_type.lower() == 'svg':
                self.fig.savefig(output_file, bbox_inches='tight', 
                               facecolor='white', edgecolor='none')
            else:
                print(f"Unsupported format: {format_type}")
                return
            
            print(f"Chart saved to: {output_file}")
            
        except Exception as e:
            print(f"Error saving chart: {e}")
    
    def show_chart(self):
        """Display the chart"""
        if self.fig is None:
            print("No chart created. Please create chart first.")
            return
        
        plt.show()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='OHLCV Data Visualization Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ohlcv_visualizer.py --input dataframe.csv --output chart.png
  python ohlcv_visualizer.py --input dataframe.csv --output chart.pdf --format pdf
  python ohlcv_visualizer.py --input dataframe.csv --output chart.svg --format svg --no-volume
  python ohlcv_visualizer.py --input dataframe.csv --output chart.png --no-sma --no-ema
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='Input CSV file containing OHLCV data')
    parser.add_argument('--output', '-o', required=True,
                       help='Output file path for the chart')
    parser.add_argument('--format', '-f', default='png',
                       choices=['png', 'pdf', 'svg'],
                       help='Output format (default: png)')
    parser.add_argument('--no-volume', action='store_true',
                       help='Hide volume subplot')
    parser.add_argument('--no-sma', action='store_true',
                       help='Hide Simple Moving Average')
    parser.add_argument('--no-ema', action='store_true',
                       help='Hide Exponential Moving Average')
    parser.add_argument('--show', action='store_true',
                       help='Display chart in addition to saving')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create visualizer and process data
    visualizer = OHLCVVisualizer()
    
    # Load data
    visualizer.load_data(args.input)
    
    # Create chart
    show_volume = not args.no_volume
    show_sma = not args.no_sma
    show_ema = not args.no_ema
    
    visualizer.create_candlestick_chart(
        show_volume=show_volume,
        show_sma=show_sma,
        show_ema=show_ema
    )
    
    # Save chart
    visualizer.save_chart(args.output, args.format)
    
    # Show chart if requested
    if args.show:
        visualizer.show_chart()


if __name__ == '__main__':
    main()
