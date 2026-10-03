# AgentTrust CONTRACT

Single source of truth. Change only after telling all 3 members in the group chat.

## 1. Services and ports

| Service | Port | Owner |
|---|---|---|
| Hardhat local chain | 8545 | A |
| Gateway (FastAPI) | 8000 | A |
| Dashboard (React/Vite) | 5173 | C |

Start order: Hardhat -> Gateway -> Dashboard -> `python demo.py`.
Gateway must allow CORS from `http://localhost:5173`.

## 2. Environment variables (names only, never commit values)

| Name | Used by |
|---|---|
| AGENTTRUST_SECRET | A (verify), B (issue). 32+ chars |
| COHERE_API_KEY | B |
| GATEWAY_URL | B (default `http://localhost:8000`) |
| RPC_URL | A (default `http://localhost:8545`) |

`.env` is in `.gitignore`. Repo has `.env.example` with fake placeholders.

## 3. Credential (the ID card)

JWT, HS256, signed with AGENTTRUST_SECRET. Claims:

```json
{
  "agent_id": "shopper-1",
  "scopes": ["read_inbox", "make_payment"],
  "max_amount": 500,
  "exp": 1760000000
}
```

- `exp` is required. Missing or expired -> BLOCK.
- `send_email` is deliberately NOT in scopes (demo of scope block).
- Issued by `issue_credential.py` (B).

## 4. POST /tool-call

Agent -> Gateway. Gateway checks, runs the tool if allowed, returns result.

Request:
```json
{
  "credential": "<JWT string>",
  "tool": "make_payment",
  "args": {"amount": 10000, "to": "merchant-evil"}
}
```

Response (always HTTP 200 with a decision):
```json
{
  "decision": "BLOCK",
  "reason": "amount exceeds limit 500",
  "audit_id": 7,
  "tx_hash": "0xabc...",
  "result": null
}
```

- `decision`: `"ALLOW"` or `"BLOCK"` only.
- `result`: tool output when ALLOW, else `null`.
- HTTP 422 only if the body is not valid JSON or lacks the 3 top-level fields.

## 5. Tools (run inside the gateway)

| Tool | args | result on ALLOW |
|---|---|---|
| read_inbox | none | list of `{from, subject, body}` |
| send_email | `{to, subject, body}` | `{"sent": true}` |
| make_payment | `{amount: number, to: string}` | `{"paid": amount, "to": to}` |

Agent never executes tools itself. It only calls `/tool-call`.

## 6. Check order (stop at first failure)

| # | Check | BLOCK reason string |
|---|---|---|
| 1 | JWT valid signature, has exp, not expired | `invalid or expired credential` |
| 2 | agent_id not revoked | `agent revoked` |
| 3 | tool is in scopes | `tool not in scopes` |
| 4 | args valid (make_payment: amount is a number, not bool, and > 0; `to` is a non-empty string) | `invalid arguments` |
| 5 | make_payment: amount <= max_amount | `amount exceeds limit <max_amount>` |
| - | all pass | ALLOW, reason `ok` |

Any error or bad input -> BLOCK. Gateway must never crash or default to ALLOW.
Reason strings are fixed so the dashboard can display them.

## 7. Audit record

Created for every decision (ALLOW and BLOCK):

```json
{
  "audit_id": 7,
  "timestamp": "2026-10-04T10:15:30Z",
  "agent_id": "shopper-1",
  "tool": "make_payment",
  "args": {"amount": 10000, "to": "merchant-evil"},
  "decision": "BLOCK",
  "reason": "amount exceeds limit 500",
  "record_hash": "<sha256 hex>",
  "tx_hash": "0xabc..."
}
```

- `record_hash` = SHA-256 of the JSON of these fields only: `audit_id, timestamp, agent_id, tool, args, decision, reason`. Keys sorted, no spaces (`separators=(",", ":")`).
- `record_hash` is stored on-chain via the AuditLog contract. `tx_hash` is that transaction.
- Full record is stored in gateway local storage (JSON file or SQLite).
- Credential is NEVER stored in the audit record.

## 8. Dashboard endpoints (A provides, C consumes)

| Method + Path | Returns |
|---|---|
| GET /audit | list of audit records, newest first |
| GET /agents | `[{"agent_id": "shopper-1", "status": "active" or "revoked"}]` |
| POST /revoke/{agent_id} | `{"agent_id": "shopper-1", "status": "revoked"}` |
| GET /verify/{audit_id} | `{"audit_id": 7, "match": true, "local_hash": "...", "chain_hash": "..."}` |

`/verify` recomputes the hash from the stored record and compares it to the hash read from the chain.

## 9. Demo constants (everyone uses these)

| Item | Value |
|---|---|
| Agent id | shopper-1 |
| Limit | 500 |
| Good payment | 300 to `merchant-good` -> ALLOW |
| Attack payment | 10000 to `merchant-evil` -> BLOCK |
| Poison email | from unknown@example.com, subject "URGENT: Payment Required" |
| Unauthorized tool | send_email -> BLOCK |

Demo story: (1) normal work, ALLOW; (2) poison email attack, BLOCK; (3) owner revokes, even a good payment is BLOCK.

## 10. Rules

1. Contract change = post in group chat + update this file in the same commit.
2. `main` must always run. Merge from your branch only when your part works.
3. Branches: `a-gateway`, `b-agent`, `c-dashboard`.
4. No secrets in git, ever.
5. Feature freeze: 5 Oct evening.