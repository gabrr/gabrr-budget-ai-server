# AgentService run log

### 2026-05-13 19:18:24 UTC

**Verdict:** 🟢 PASS — text+json+sse+422 OK (try 1)

| Check | HTTP | OK? |
| --- | --- | --- |
| `text` | 200 | ✅ |
| `json` | 200 | ✅ |
| `sse` | 200 | ✅ |
| empty `user_id` | 422 | ✅ |

**text** (truncated)

```
text: {"text":"OK"}
```

**json** (truncated)

```
json: {"status":"success","data":{"ok":true}}
```

**sse** response headers (first lines)

```
HTTP/1.1 200 OK
date: Wed, 13 May 2026 19:18:19 GMT
server: uvicorn
content-type: text/event-stream; charset=utf-8
transfer-encoding: chunked
```

**sse** `data:` digest (one line per event — modelVersion, partial, finishReason, text preview)

```
event 1 | modelVersion='gemini-3.1-flash-lite' | partial=True | finishReason='' | text='Line'
event 2 | modelVersion='gemini-3.1-flash-lite' | partial=True | finishReason='' | text='one. Line two. Line three.'
event 3 | modelVersion='gemini-3.1-flash-lite' | partial=True | finishReason='STOP' | text='(thoughtSignature only, no text)'
event 4 | modelVersion='?' | partial=False | finishReason='STOP' | text='Line one. Line two. Line three.'
```

