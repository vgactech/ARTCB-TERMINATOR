# ARTCB-TERMINATOR

Dépôt de rapports et de code de sécurité Guardian pour le projet ARTCB.

## Structure

```
rapports/           Rapports R001–R013 + prompts
guardian_core/      C-01 à C-08 — Rust Security Core (+ binding PyO3)
guardian_mcp/       C-07 — Instrumentation MCP Python
guardian_api/       FastAPI bridge for the Guardian web console
frontend/           React + TypeScript Guardian dashboard
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

## Run the integrated console

Use two PowerShell windows from the repository root.

Backend:

```powershell
python -m pip install -r guardian_api\requirements.txt
python -m uvicorn guardian_api.app:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm.cmd run dev
```

Open `http://localhost:5173`. The dashboard checks backend health, loads four
policy scenarios, and shows the real Guardian decision, events, evidence, replay,
and tamper-verification result for every run.

Run the Python and API tests with:

```powershell
python -m pytest guardian_api guardian_mcp -q
```
