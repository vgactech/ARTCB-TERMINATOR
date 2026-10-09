# ARTCB-TERMINATOR

Dépôt de rapports et de code de sécurité Guardian pour le projet ARTCB.

## Structure

```
rapports/           Rapports R001–R013 + prompts
guardian_core/      C-01 à C-08 — Rust Security Core (+ binding PyO3)
guardian_mcp/       C-07 — Instrumentation MCP Python
```

## Composants

| ID   | Nom                    | Langage      | Tests |
|------|------------------------|--------------|-------|
| C-01 | Event Ledger           | Rust         | ✅ 7  |
| C-02 | Durable Event Store    | Rust         | ✅ 3  |
| C-03 | Provenance Graph       | Rust         | ✅ 3  |
| C-04 | Secure Agent Channel   | Rust         | ✅ 7  |
| C-05 | Policy Engine          | Rust         | ✅ 5  |
| C-06 | Replay Engine          | Rust         | ✅ 2  |
| C-07 | MCP Instrumentation    | Python       | ✅ 17 |
| C-08 | PyO3 Bindings          | Rust + Python| structure |

## Golden F-001 (R006)

Digest SHA-256 confirmé : `c067e20378788d5d32e25c489064efd624224596c1987b5315f8dde296892f11`

## Build

```bash
cd guardian_core
cargo test          # 27 tests Rust

cd ../guardian_mcp
python3 -m pytest test_instrumentation.py -v   # 17 tests Python
```
