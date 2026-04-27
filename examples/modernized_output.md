# CodeSage — Example Output

**Input:** `examples/legacy_sample.js` (TC-01: Callback Hell)
**Agent Run Time:** 8.7s

---

## 🔍 Analysis Summary

**Files Analyzed:** 1  
**Issues Found:** 3 (CRITICAL: 0, HIGH: 0, MEDIUM: 2, LOW: 1)

---

## 🟡 Medium Issues

### Issue 1: Callback Hell (CWE-1120 — Excessive Code Complexity)

**File:** `examples/legacy_sample.js`  
**Lines:** 5–38  
**Risk:** 🟡 MEDIUM

**Root Cause:** 5-level deep callback nesting — a pattern common in Node.js pre-2015, before `Promise` (ES6) and `async/await` (ES2017) were available. The original author was constrained by the Node.js 0.10 era, which had no built-in async primitives.

**Impact:**
- Any error in the middle levels silently drops (only the first `err` check works)
- Impossible to unit test inner callbacks in isolation
- Cognitive load: you must hold 5 levels of context in your head simultaneously
- Refactoring risk: high — each level is tightly coupled to the next

**Fix — async/await (ES2017+):**

```javascript
import { readFile, writeFile } from 'fs/promises';

/**
 * Fetches and caches combined user data (profile + orders).
 * @param {string} userId
 * @returns {Promise<{user: object, profile: object, orders: object[]}>}
 */
async function processUserData(userId) {
  // Read user from disk
  const raw = await readFile(`users/${userId}.json`, 'utf8');
  const user = JSON.parse(raw);

  // Fetch profile and orders in parallel (2× faster than sequential)
  const [profileRes, ordersRes] = await Promise.all([
    fetch(`https://api.example.com/profile/${userId}`),
    fetch(`https://api.example.com/orders/${userId}`),
  ]);

  if (!profileRes.ok) throw new Error(`Profile fetch failed: ${profileRes.status}`);
  if (!ordersRes.ok)  throw new Error(`Orders fetch failed: ${ordersRes.status}`);

  const [profile, orders] = await Promise.all([
    profileRes.json(),
    ordersRes.json(),
  ]);

  const result = { user, profile, orders };

  // Write cache
  await writeFile(`cache/${userId}.json`, JSON.stringify(result));

  return result;
}
```

**Additional Steps:**
1. Replace `http.get` with `fetch` (built-in Node 18+) or `axios`
2. Add a try/catch at the call site or use a global error boundary
3. Add JSDoc types or migrate to TypeScript for the return shape
4. Add test: `test('processUserData returns combined data', async () => {...})`

---

### Issue 2: No Error Propagation in Nested Callbacks

**File:** `examples/legacy_sample.js`  
**Lines:** 15–35  
**Risk:** 🟡 MEDIUM

**Root Cause:** Only the outermost `fs.readFile` callback checks for errors. HTTP failures inside the nested callbacks are silently swallowed.

**Impact:** A network failure fetching orders returns `undefined` orders, potentially crashing downstream consumers.

**Fix:** Covered by the async/await rewrite above — `Promise.all` propagates rejections automatically.

---

## 🟢 Low Issues

### Issue 3: Missing JSDoc / Type Annotations

**File:** `examples/legacy_sample.js`  
**Lines:** 4–5  
**Risk:** 🟢 LOW

No documentation on the callback signature `(err, result)`. Covered in the fix above.

---

## 🔄 Recommended Modernization Plan

**Phase 1 (Do Now — 1 hour):**
- Add error handling for all HTTP calls
- Wrap call sites in try/catch

**Phase 2 (This Sprint — 4 hours):**
- Convert to async/await (fix above)
- Parallelize profile + orders with `Promise.all` (2× speed gain)

**Phase 3 (Next Quarter):**
- Migrate to TypeScript for type safety
- Replace cache with Redis TTL cache

**Estimated Total Effort:** Small (< 1 day)  
**Risk Level:** 🟡 MEDIUM (behavior change — test before deploying)
