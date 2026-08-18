# PROJECT ARGUS
### Adaptive Real-time Gold Understanding System

A modular Decision Intelligence System for XAUUSD, built on MetaTrader 5 —
not a simple Expert Advisor. Combines ICT (Inner Circle Trader) concepts
(liquidity sweeps, Fair Value Gaps) with RSI confirmation, wrapped in a
professional, observable, and safety-governed architecture.

---

## Status: Phase 1 — Foundation

Phase 1 delivers the professional foundation: logging, configuration,
folder management, the event bus, system status tracking, the MT5
read-only bridge, the scanner scheduling framework, the empty
Evidence/Decision/Risk engine contracts, the Guardian safety layer, the
daily journal, and the live terminal dashboard.

**No trading logic executes yet.** Strategy detection (liquidity sweeps,
FVGs, RSI confirmation) and order execution are intentionally left as
Phase 2+ work — see `docs/` for the roadmap.

---

## Project Structure

```
PROJECT_ARGUS/
├── src/
│   ├── core/          # Logger, ConfigManager, EventManager, FolderManager, SystemStatus
│   ├── dashboard/      # Live terminal dashboard (rich)
│   ├── mt5/            # MT5 connection bridge (read-only: connect, tick, candles, symbol info)
│   ├── scanner/         # Scanner scheduling framework (strategy-agnostic)
│   ├── engine/           # Evidence Engine, Decision Engine, Risk Manager (skeletons)
│   ├── guardian/          # Safety oversight / kill-switch
│   ├── journal/            # Daily journal (CSV/JSON)
│   └── utils/               # Shared helpers (session detection, formatting)
├── config/
│   └── config.yaml     # All runtime configuration
├── docs/                # Architecture & roadmap notes
├── tests/                # Unit tests
├── logs/                  # Daily rotating log files (auto-created)
├── run.py                  # Application entry point
├── requirements.txt
└── .gitignore
```

---

## Requirements

- **OS:** Windows 11 (MetaTrader5 Python package is Windows-only)
- **Python:** 3.13
- **MT5 Terminal:** Installed and logged into a broker (demo recommended)
- **IDE:** VS Code (recommended)

---

## Setup

1. **Clone / extract the project**

2. **Create a virtual environment**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure your account**

   Edit `config/config.yaml`:
   ```yaml
   mt5:
     account: 12345678
     password: "your-password"
     server: "YourBroker-Demo"
     symbol: "XAUUSD"
   ```

5. **Run the application**
   ```powershell
   python run.py
   ```

   If MT5 is unreachable (e.g. running this on a non-Windows dev machine,
   or the terminal isn't open), ARGUS boots in **offline mode**: the
   dashboard and architecture run normally, but the scanner will not
   start until a connection is established.

---

## Configuration Reference (`config/config.yaml`)

| Section     | Key                          | Description                                      |
|-------------|-------------------------------|---------------------------------------------------|
| `mt5`       | `account`, `password`, `server` | Broker login credentials                          |
| `mt5`       | `symbol`                      | Trading instrument (default `XAUUSD`)              |
| `mt5`       | `timeframe_entry`               | Entry timeframe (default `M3`)                     |
| `mt5`       | `timeframe_structure`             | Market structure timeframe (default `M15`)          |
| `mt5`       | `lot`                             | Fixed lot size                                      |
| `mt5`       | `spread_limit_points`               | Guardian spread ceiling                             |
| `risk`      | `fixed_loss_per_trade`                | Fixed floating loss (account currency) driving SL   |
| `risk`      | `reward_to_risk`                        | TP multiple of risk (default `2.0` → 1:2)           |
| `strategy`  | `rsi_overbought` / `rsi_oversold`         | RSI confirmation thresholds (75 / 25)               |
| `filters`   | `news_filter_enabled`                       | Enable/disable the news blackout filter             |
| `scanner`   | `interval_seconds`                            | Scanner polling interval                             |

---

## Architecture Principles

- **Clean separation of concerns** — each module owns exactly one
  responsibility (connection, scanning, evidence, decision, risk, safety).
- **No trading without Guardian approval** — the Guardian is the single
  authority allowed to halt the system; the Decision Engine never
  executes trades directly.
- **Read-only MT5 bridge in Phase 1** — order placement is deliberately
  absent until the Engine layer is complete and tested.
- **Fully typed, documented, logged** — every public method has type
  hints, a docstring, and structured logging.

---

## Roadmap

- **Phase 2:** Implement Evidence Engine detectors (liquidity sweep, FVG,
  RSI confirmation) and Decision Engine scoring logic.
- **Phase 3:** Implement Risk Manager SL/TP price calculation via MT5
  symbol info (point value, contract size) and wire order execution
  behind the Guardian.
- **Phase 4:** Forward-test on demo account; iterate on thresholds.

---

## License

Proprietary — internal trading research project.
