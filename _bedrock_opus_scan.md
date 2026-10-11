# Bedrock Claude Sonnet 4.5 — Scan ARTCB-TERMINATOR

## SCAN 1 — Security + KYC bug

# ARTCB TERMINATOR FORENSIC — Security Analysis

## A. GUARDIAN SECURITY — Real vulnerabilities

### 1. **Critical: R0 Chain Integrity Compromised (instrumentation.py)**
**Location**: `guardian_mcp/instrumentation.py:~100` (to_canonical_dict method is **truncated**)

The `to_canonical_dict()` method that produces the canonical body for SHA-256 chaining is **cut off mid-implementation**. This breaks the entire R0 chain guarantee:

```python
def to_canonical_dict(self) -> dict[str, Any]:
    """Corps canonique JCS-compatible (clés triées récursivement)...
    R033-A : event_phase et intent_id sont inclus dans le corps canonique.
    """
    # METHOD BODY MISSING - CODE TRUNCATED
```

**Impact**: Without the canonical dict implementation:
- `previous_event_hash` cannot be computed correctly
- Chain verification in `verify_chain_r0()` will always fail or pass trivially
- Attackers can inject/reorder events without detection
- R023-002 compliance (cryptographic chaining) is **impossible**

### 2. **Race Condition: INTENT/TERMINAL Phase Mismatch (instrumentation.py + defender_agent.py)**
**Location**: `guardian_mcp/instrumentation.py:~75-85` + `defender_agent.py:~140-165`

The two-phase commit (INTENT before execution, TERMINAL after) has no atomic guarantees:

```python
# defender_agent.py:~145
before = self._executor_call_count
mcp_result = self._instrumentation.handle_tool_call(
    params=exfil_call.to_mcp_params(),
    executor=self._dangerous_executor,
)
after = self._executor_call_count
tool_executed = after >  # TRUNCATED - likely `after > before`
```

**Vulnerability**: If the process crashes between INTENT logging and TERMINAL logging:
1. INTENT event is recorded with `event_phase="INTENT"`
2. Tool executes (or doesn't)
3. **Crash occurs**
4. No TERMINAL event recorded
5. On restart, R033-E requires classifying as `IN_DOUBT`, but code shows no recovery mechanism

**Attack vector**: Attacker triggers OOM/kill signal after INTENT but before TERMINAL → permanent `IN_DOUBT` state → audit trail breaks.

### 3. **Policy Bypass: executor_call_count is Bypassable (defender_agent.py:~145)**
**Location**: `defender_agent.py:~75-80, ~145-150`

```python
# defender_agent.py:~145
before = self._executor_call_count
mcp_result = self._instrumentation.handle_tool_call(...)
after = self._executor_call_count
tool_executed = after >  # TRUNCATED
```

The `_executor_call_count` is a **simple integer incremented by `_dangerous_executor`**. Problems:

1. **No cryptographic binding**: Count can be manipulated if `_dangerous_executor` is mocked/replaced
2. **Assumes single-threaded**: Concurrent calls will corrupt the count
3. **No validation in C-07 layer**: `GuardianMCPInstrumentation` doesn't verify execution independently

**Bypass**: Malicious code can:
```python
defender._executor_call_count = 0  # Reset before check
# Now tool_executed = False even if tool ran
```

### 4. **False Negative: EvidenceId Generation Without Verification (defender_agent.py:~21-28)**
**Location**: `defender_agent.py:~145-165` (attempt_tool_call)

```python
# R021-003 : l'EvidenceId est un UUID distinct généré par cet agent
# pour chaque décision BLOCK. Il est explicitement lié à l'event_id
# Guardian retourné par C-07. Ce n'est pas le hash de l'événement.
```

The code generates `evidence_id = str(uuid.uuid4())` for BLOCK decisions, but:

1. **No verification** that the event was actually logged before returning EvidenceId
2. **No check** that `mcp_result` contains valid `event_id`
3. If C-07 fails silently, caller still gets an EvidenceId → **false proof of blocking**

**Impact**: Agent D can claim "attack blocked with evidence XYZ" when no Guardian event exists.

---

## B. KYC BLANK PAGE — Precise diagnosis

### Root Cause: EventSource event handlers truncated (KycPanel.tsx:~180+)

**Location**: `frontend/src/components/KycPanel.tsx:~178-180`

```typescript
es.addEventListener('attack_generated', (e: MessageEvent) => {
  // ... handler code ...
})
es.addE  // TRUNCATED - likely `es.addEventListener(...)`
```

**The file is cut off** mid-handler registration. Critical missing handlers:

1. **`'kyc_result'` event**: Contains final verdict/score/PDF → `setResult()` never called
2. **`'done'` event**: Sets `setRunning(false)` → UI stuck in loading state
3. **`'error'` event**: Error handling missing → silent failures
4. **Default `'error'`/`'close'` handlers**: Network failures unhandled

### Why Blank Page Happens:

1. User clicks "Lancer KYC complet" → `runKyc()` called
2. `setRunning(true)` → Shows loading spinner/disables form
3. EventSource connects, receives initial events (`session_opened`, `kyc_identity_check`)
4. Backend sends `kyc_result` SSE event with PDF data
5. **No handler registered** → event ignored
6. `setResult(null)` remains → no verdict rendered
7. `setRunning(true)` remains → UI frozen in loading state
8. Blank screen with spinner (or blank if spinner conditional on `result`)

### Minimal Fix:

**Add before line 180** (after last visible `addEventListener`):

```typescript
es.addEventListener('kyc_result', (e: MessageEvent) => {
  const d = JSON.parse(e.data) as KycResult
  dispatch('kyc_result', d as KycStreamEvent)
  setResult(d)
  if (d.pdf_base64) {
    const blob = new Blob(
      [Uint8Array.from(atob(d.pdf_base64), c => c.charCodeAt(0))],
      { type: 'application/pdf' }
    )
    setPdfUrl(URL.createObjectURL(blob))
  }
  addEntry({ 
    type: 'done', 
    label: `Verdict: ${d.verdict}`, 
    detail: `Score ${d.score}% | ${d.attacks_blocked} attaques bloquées`, 
    status: d.verdict === 'APPROVED' ? 'ok' : 'fail' 
  })
})

es.addEventListener('done', () => {
  setRunning(false)
  es.close()
})

es.onerror = () => {
  addEntry({ type: 'error', label: 'Erreur SSE', detail: 'Connexion perdue', status: 'fail' })
  setRunning(false)
  es.close()
}
```

---

## C. CODE QUALITY — Max 3 critical bugs

### 1. **kyc_stream.py:~95 — Variable name typo in `_minimal_pdf`**
**Location**: `guardian_api/kyc_stream.py:~95`

```python
def _minimal_pdf(
    first_name: str, last_name: str, doc_id: str,
    verdict: str, sc  # TRUNCATED - should be `score: int, ...`
```

**Bug**: Parameter list cut off, likely `sc` instead of `score: int`. Fallback PDF generation will **crash** with `NameError: name 'score' is not defined` when fpdf2 is unavailable.

**Fix**: `score: int, attacks_blocked: int, session_id: str, timestamp: str`

---

### 2. **defender_agent.py:~150 — Comparison operator truncated**
**Location**: `guardian_mcp/defender_agent.py:~150`

```python
tool_executed = after >  # TRUNCATED
```

**Bug**: Incomplete boolean expression. Will cause **SyntaxError** at runtime. Should be:

```python
tool_executed = after > before
```

**Impact**: Agent D's `attempt_tool_call()` cannot execute → entire defense mechanism fails at import time.

---

### 3. **KycPanel.tsx:~55 — Form validation bypasses empty values**
**Location**: `frontend/src/components/KycPanel.tsx:~55-62`

```typescript
function runKyc() {
  // Validation : refuser la soumission si tous les champs sont vides
  if (!firstName.trim() && !lastName.trim() && !docId.trim() && !dob.trim()) {
    addEntry({ type: 'error', label: 'Formulaire vide', ... })
    return
  }
```

**Bug**: Validation uses **AND (`&&`)** instead of **OR (`||`)**. Current logic only rejects if **all four fields** are empty. User can submit with only firstName filled → backend receives partial data.

**Expected**: Reject if any required field is empty:
```typescript
if (!firstName.trim() || !lastName.trim() || !docId.trim() || !dob.trim()) {
```

**Impact**: Invalid KYC requests reach backend, wasting compute resources and producing incomplete audit trails.

---

