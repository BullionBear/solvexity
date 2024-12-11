
# solvexity

**solvexity** is a crypto trading bot designed to help traders execute disciplined live trading while leveraging their financial and mathematical expertise. It provides a modular and extensible framework for analyzing, diagnosing, and improving trading strategies.

---

## Purpose

1. **Execute Live Trading Discipline**  
   Maintain a systematic and consistent approach to trading, reducing emotional or impulsive decisions.

2. **Leverage Financial & Mathematical Knowledge**  
   Integrate advanced financial theories and mathematical models for informed decision-making.

3. **Modular Trading Diagnosis**  
   Facilitate the evaluation and optimization of trading components through a flexible and modular architecture.

---

## Architecture

The architecture of **solvexity** consists of two key parts:  
1. **Data**: Collecting, processing, and providing accurate market information.  
2. **Decision Making**: Generating actionable insights and executing trades based on the processed data.

---

### Components

#### **Trader/Core**  
The core library providing abstracted components for building and executing crypto trading strategies.

- **Data Provider**  
  - Collects real-time market data.  
  - Pushes data to Redis as a centralized data source for other components.  

- **Signal**  
  - Converts market data into actionable signals: **Buy**, **Hold**, or **Sell**.  
  - Employs algorithms or models to identify trading opportunities.

- **Policy**  
  - Interprets signals and converts them into market actions.  
  - Implements risk management, order placement, and execution logic.

---

## Usage

The modular design allows you to customize each component independently, making **solvexity** suitable for traders at any level, from beginners to advanced quantitative traders.

## Run the process

### Before execute
```
python infra/log_aggregator.py --log-dir ./log
```