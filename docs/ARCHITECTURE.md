# PROJECT ARGUS — Architecture Notes

## Data / Control Flow (Phase 1)

```
            ┌────────────────┐
            │   config.yaml   │
            └────────┬────────┘
                     │
              ConfigManager
                     │
      ┌──────────────┼───────────────┐
      │              │               │
 FolderManager   ArgusLogger    EventManager
      │              │               │
      └──────────────┴───────────────┘
                     │
              SystemStatusManager
                     │
      ┌──────────────┼───────────────────────┐
      │              │                        │
  MT5Bridge  ──►  Scanner  ──►  EvidenceEngine (stub)
      │              │                        │
      │              │                 DecisionEngine (stub)
      │              │                        │
      │              │                  RiskManager (stub)
      │              │                        │
      │              └──────────────►    Guardian
      │                                        │
      └───────────────────────►          DailyJournal
                                                │
                                          Dashboard (live render)
```

## Design Decisions

1. **Singletons for cross-cutting concerns.** `ConfigManager`,
   `EventManager`, and `SystemStatusManager` are process-wide singletons
   so every module observes one consistent state without manual wiring.

2. **Event bus decouples subsystems.** The Scanner does not call the
   Dashboard directly; it publishes events (`scanner.tick`,
   `guardian.halt`, etc.) that any subscriber can react to. This keeps
   Phase 2/3 additions low-risk — new subscribers can be added without
   touching existing publishers.

3. **Guardian has veto power, not the Decision Engine.** Even once
   strategy logic is implemented, the Decision Engine only *proposes* a
   trade; the Guardian's spread/loss/connection checks gate whether the
   (future) execution layer is allowed to act on it.

4. **MT5 bridge is read-only in Phase 1 by design.** This lets the team
   validate connectivity, data quality, and the dashboard end-to-end on
   a demo account before any execution code is written.

## Phase 2 Preview: Evidence Contract

`EvidenceEngine.analyze()` will populate `EvidenceItem` objects such as:

```python
EvidenceItem(
    kind="LIQUIDITY_SWEEP",
    details={"swept_level": 2412.10, "direction": "BEARISH", "candle_index": 42},
)
EvidenceItem(
    kind="FVG",
    details={"gap_high": 2413.40, "gap_low": 2412.90, "filled": False},
)
EvidenceItem(
    kind="RSI_CONFIRMATION",
    details={"rsi": 78.4, "state": "OVERBOUGHT"},
)
```

The Decision Engine will then score combinations of these into a
`Decision(state=BUY|SELL|WAIT, confidence=0.0-1.0)`.
