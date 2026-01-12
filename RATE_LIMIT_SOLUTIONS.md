# Google Sheets API Rate Limit Solutions

## Executive Summary

Your application is hitting the **"Read requests per minute per user"** quota limit (60 requests/minute/user). After analyzing your codebase and researching Google Sheets API best practices, I've identified the root causes and present several solutions ranked by impact and implementation effort.

---

## Current Rate Limits

Based on official Google documentation:

| Quota Type | Limit | Your Issue |
|------------|-------|------------|
| **Read requests per minute per user** | 60 | **← You're hitting this** |
| Read requests per minute per project | 300 | Not yet reached |
| Write requests per minute per user | 60 | Likely not an issue |
| Write requests per day | Unlimited | No concern |

**Key Insight**: The quota refills every minute, so if you exceed 60 reads in a minute, you must wait until the next minute for the quota to reset.

---

## Root Cause Analysis

After reviewing your code, here are the primary sources of excessive read requests:

### 1. **Individual Cell Reads for Metadata (CRITICAL ISSUE)**

**Location**: `src/sheet_updater.py:75-144` (`_build_sheet_metadata_cache`)

```python
for sheet in sheets:
    # This reads cell A1 INDIVIDUALLY for each sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A1"
    ).execute()
```

**Problem**: If you have 16 teams, this makes **16 separate read API calls** just to build the metadata cache. This happens on EVERY update.

**Impact**: With 16 teams, you're using 26% of your quota (16/60) just for this operation.

---

### 2. **Redundant Reads in Orphaned Sheet Cleanup**

**Location**: `src/sheet_updater.py:328-462` (`cleanup_orphaned_sheets`)

```python
for sheet in sheets:
    # ANOTHER individual read of cell A1 for EVERY sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A1"
    ).execute()
```

**Problem**: This function reads the SAME cell A1 data that `_build_sheet_metadata_cache` already read, resulting in **duplicate API calls**.

**Impact**: Another 16 reads for a 16-team league (32 total between both functions).

---

### 3. **Multiple Individual Operations**

Throughout your update workflow:
- Reading timestamp from Summary!G1 (1 read)
- Validating sheet structure (1 read)
- Getting existing team sheets (1 read)
- Individual team sheet lookups when not found in cache
- Reading Summary sheet data before clearing

**Impact**: 5-10 additional reads per update cycle.

---

## Recommended Solutions

### **SOLUTION 1: Use Batch Read API (HIGHEST IMPACT, MEDIUM EFFORT)**

**Priority**: 🔴 CRITICAL - Implement this first

Google provides `spreadsheets.values.batchGet` which allows reading multiple ranges in a **single API call**.

#### How It Works

Instead of:
```python
# 16 separate API calls (16/60 quota used)
for sheet_title in sheet_titles:
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A1"
    ).execute()
```

Do this:
```python
# 1 API call for all sheets (1/60 quota used)
ranges = [f"'{sheet_title}'!A1" for sheet_title in sheet_titles]
result = service.spreadsheets().values().batchGet(
    spreadsheetId=spreadsheet_id,
    ranges=ranges
).execute()

value_ranges = result.get('valueRanges', [])
# Process all results at once
```

#### Expected Impact

- **Before**: 32 read requests (metadata + cleanup) for 16 teams
- **After**: 1 read request for all metadata
- **Quota Savings**: 97% reduction (31 fewer API calls)

#### Implementation Areas

1. **`_build_sheet_metadata_cache`** (lines 75-144)
   - Replace individual `values().get()` calls with single `values().batchGet()`
   - Build ranges list for all sheets upfront
   - Parse results from returned `valueRanges` array

2. **`cleanup_orphaned_sheets`** (lines 328-462)
   - Reuse metadata cache from `_build_sheet_metadata_cache` instead of re-reading
   - OR use `batchGet` if cache not available

3. **Initial sheet reads**
   - Combine timestamp read (G1) + structure validation into single `batchGet`

#### Code Example

```python
def _build_sheet_metadata_cache_batch(service: Any, spreadsheet_id: str) -> dict:
    """
    Build metadata cache using batch read (1 API call instead of N calls).
    """
    try:
        # Get all sheets
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        sheets = spreadsheet.get('sheets', [])

        # Build ranges list for batch read
        ranges = []
        sheet_info = []  # Track sheet_id and title for each range

        for sheet in sheets:
            properties = sheet.get('properties', {})
            sheet_title = properties.get('title')

            if sheet_title == 'Summary':
                continue

            sheet_id = properties.get('sheetId')
            ranges.append(f"'{sheet_title}'!A1")
            sheet_info.append((sheet_id, sheet_title))

        if not ranges:
            return {}

        # SINGLE batch read for all sheets
        result = service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=ranges
        ).execute()

        # Process results
        metadata_cache = {}
        value_ranges = result.get('valueRanges', [])

        for i, value_range in enumerate(value_ranges):
            sheet_id, sheet_title = sheet_info[i]
            values = value_range.get('values', [])

            if values and values[0]:
                cell_value = str(values[0][0])
                if cell_value.startswith('TEAM_ID:'):
                    team_id = cell_value.split(':', 1)[1].strip()
                    metadata_cache[team_id] = (sheet_id, sheet_title)

        logger.debug(f"Built metadata cache with {len(metadata_cache)} entries using 1 API call")
        return metadata_cache

    except HttpError as e:
        error_msg = f"Failed to build sheet metadata cache: {e}"
        logger.error(error_msg)
        raise SheetUpdateError(error_msg) from e
```

---

### **SOLUTION 2: Cache Metadata Across Functions (HIGH IMPACT, LOW EFFORT)**

**Priority**: 🟡 HIGH - Quick win, pair with Solution 1

#### Current Problem

`_build_sheet_metadata_cache` and `cleanup_orphaned_sheets` both read the same cell A1 data independently.

#### Solution

Pass the metadata cache as a parameter instead of re-reading:

```python
def cleanup_orphaned_sheets(
    service: Any,
    spreadsheet_id: str,
    current_team_ids: set,
    current_team_names: set,
    metadata_cache: dict = None  # ADD THIS PARAMETER
) -> int:
    """
    Use pre-built metadata cache instead of re-reading cells.
    """
    if metadata_cache is None:
        # Fallback: build cache if not provided
        metadata_cache = _build_sheet_metadata_cache(service, spreadsheet_id)

    # Now use metadata_cache instead of reading cells again
    # ... rest of function
```

#### Expected Impact

- **Before**: 32 reads (16 in cache build + 16 in cleanup)
- **After**: 16 reads (cache reused)
- **Quota Savings**: 50% reduction

#### Combined with Solution 1

If you implement both Solution 1 AND Solution 2:
- **Total reads**: 1 (batch read) + 0 (cache reuse) = **1 API call**
- **Quota Savings**: 97% reduction (31 fewer calls)

---

### **SOLUTION 3: Exponential Backoff with Retry (MEDIUM IMPACT, LOW EFFORT)**

**Priority**: 🟢 MEDIUM - Safety net, doesn't reduce calls but handles limits gracefully

#### How It Works

When you hit a 429 error (rate limit exceeded), automatically wait and retry with exponentially increasing delays.

#### Implementation

Google's recommended formula:
```
wait_time = min(((2^n) + random_milliseconds), maximum_backoff)
```

Where:
- `n` starts at 0, increments by 1 for each retry
- `random_milliseconds` is 0-1000ms (prevents thundering herd)
- `maximum_backoff` is typically 32-64 seconds

#### Code Example

```python
import time
import random
from googleapiclient.errors import HttpError

def api_call_with_retry(api_function, max_retries=5, max_backoff=64):
    """
    Execute Google Sheets API call with exponential backoff retry.

    Args:
        api_function: Lambda or function that makes the API call
        max_retries: Maximum number of retry attempts (default: 5)
        max_backoff: Maximum backoff time in seconds (default: 64)

    Returns:
        API call result

    Raises:
        HttpError: If all retries exhausted
    """
    for attempt in range(max_retries):
        try:
            return api_function()
        except HttpError as e:
            # Only retry on 429 (rate limit) or 5xx (server errors)
            if e.resp.status not in [429, 500, 502, 503, 504]:
                raise

            if attempt == max_retries - 1:
                # Last attempt, re-raise error
                raise

            # Calculate exponential backoff
            wait_time = min(
                (2 ** attempt) + (random.randint(0, 1000) / 1000),
                max_backoff
            )

            logger.warning(
                f"Rate limit hit (429). Retrying in {wait_time:.2f}s "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(wait_time)

    raise HttpError(f"Max retries ({max_retries}) exceeded")

# Usage example
result = api_call_with_retry(
    lambda: service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Summary!G1'
    ).execute()
)
```

#### Expected Impact

- **Quota Savings**: None (same number of requests)
- **Reliability**: Prevents crashes, auto-recovers from rate limits
- **User Experience**: Transparent handling, operation completes successfully

---

### **SOLUTION 4: Strategic Delays Between Operations (LOW IMPACT, LOW EFFORT)**

**Priority**: 🟢 LOW - Last resort, not recommended as primary solution

#### Why This Is Less Ideal

- Slows down your application unnecessarily
- Doesn't actually solve the root cause (inefficient API usage)
- If you implement Solutions 1-2, delays become unnecessary

#### When To Use

Only if you CANNOT implement batch reads and need a quick temporary fix.

#### Implementation

```python
import time

# Add delay between operations
def update_team_sheets_with_throttling(teams):
    for i, team in enumerate(teams):
        update_team_sheet(service, spreadsheet_id, team)

        # Throttle: wait 1 second between updates
        if i < len(teams) - 1:  # Don't wait after last team
            time.sleep(1)
```

#### Trade-offs

- **For 16 teams**: Adds 15-16 seconds to total runtime
- **Quota Impact**: Spreads requests over time, may avoid 60/minute limit
- **Downside**: Much slower user experience

---

### **SOLUTION 5: Use spreadsheets.get() for Metadata (MEDIUM IMPACT, LOW EFFORT)**

**Priority**: 🟡 MEDIUM - Alternative to batch reads

#### Current Issue

You're making separate API calls to read cell values (`values().get()`). However, the `spreadsheets().get()` method can return cell values AND sheet structure in ONE call.

#### How It Works

```python
# Instead of this (multiple API calls):
# 1. Get sheet list
spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

# 2. Read each sheet's A1 cell (16 more API calls for 16 teams)
for sheet_title in sheet_titles:
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A1"
    ).execute()

# Do this (1 API call with includeGridData):
spreadsheet = service.spreadsheets().get(
    spreadsheetId=spreadsheet_id,
    includeGridData=True,
    ranges=['Team1!A1', 'Team2!A1', 'Team3!A1']  # Specify ranges
).execute()

# Access both metadata AND cell values from single response
for sheet in spreadsheet.get('sheets', []):
    sheet_title = sheet['properties']['title']
    # Cell data is in sheet['data'][0]['rowData'][0]['values'][0]['formattedValue']
```

#### Trade-offs

- **Pro**: Single API call, includes structure + data
- **Con**: Response parsing is more complex
- **Con**: includeGridData responses are larger (more bandwidth)

#### When To Use

If you need BOTH sheet structure and cell values together, this can be more efficient than `batchGet`.

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1)

1. ✅ **Implement Solution 2** (Cache reuse)
   - Modify `cleanup_orphaned_sheets` to accept metadata cache parameter
   - Pass cache from `_build_sheet_metadata_cache` to `cleanup_orphaned_sheets`
   - **Effort**: 30 minutes
   - **Impact**: 50% reduction in metadata reads

2. ✅ **Implement Solution 3** (Exponential backoff)
   - Create `api_call_with_retry` wrapper function
   - Wrap all `.execute()` calls with retry logic
   - **Effort**: 1-2 hours
   - **Impact**: Prevents crashes, graceful degradation

### Phase 2: Core Optimization (Week 2)

3. ✅ **Implement Solution 1** (Batch reads)
   - Refactor `_build_sheet_metadata_cache` to use `batchGet`
   - Update `read_last_run_timestamp` + structure validation to use `batchGet`
   - Test with your 16-team league
   - **Effort**: 3-4 hours
   - **Impact**: 97% reduction in metadata reads (32 → 1 call)

### Phase 3: Advanced (Optional)

4. ⚠️ **Consider Solution 5** (spreadsheets.get with includeGridData)
   - Only if you need to further optimize and want single-call approach
   - Requires more significant refactoring
   - **Effort**: 4-6 hours
   - **Impact**: Marginal additional improvement

---

## Expected Results

### Current State (Before Optimization)

For a 16-team league update:
- **Metadata cache build**: 16 read requests
- **Orphaned sheet cleanup**: 16 read requests
- **Timestamp read**: 1 read request
- **Structure validation**: 1 read request
- **Other reads**: ~5 read requests
- **TOTAL**: ~39 read requests per update

**Risk**: With 39 reads per update, if you update twice in a minute or have concurrent operations, you'll hit the 60/minute limit.

### After Phase 1 (Cache Reuse + Retry)

- **Metadata cache build**: 16 read requests
- **Orphaned sheet cleanup**: 0 (reuses cache) ← SAVED 16
- **Timestamp read**: 1 read request
- **Structure validation**: 1 read request
- **Other reads**: ~5 read requests
- **TOTAL**: ~23 read requests per update

**Improvement**: 41% reduction, can handle 2 updates/minute safely

### After Phase 2 (Batch Reads)

- **Metadata cache build**: 1 batch read ← SAVED 15 more
- **Orphaned sheet cleanup**: 0 (reuses cache)
- **Initial reads (timestamp + validation)**: 1 batch read ← SAVED 1
- **Other reads**: ~5 read requests
- **TOTAL**: ~7 read requests per update

**Improvement**: 82% reduction, can handle 8+ updates/minute safely

---

## Testing Strategy

### 1. Unit Tests

Test the new batch read functions:

```python
def test_batch_metadata_read():
    """Test that batch read returns same results as individual reads."""
    # Get results from old method
    old_cache = _build_sheet_metadata_cache_old(service, spreadsheet_id)

    # Get results from new batch method
    new_cache = _build_sheet_metadata_cache_batch(service, spreadsheet_id)

    # Compare
    assert old_cache == new_cache
```

### 2. Rate Limit Stress Test

Create a test that intentionally hits rate limits:

```python
def test_rate_limit_handling():
    """Test that exponential backoff handles rate limits gracefully."""
    # Make 70 rapid API calls (exceeds 60/minute limit)
    for i in range(70):
        result = api_call_with_retry(
            lambda: service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'Summary!A{i+1}'
            ).execute()
        )

    # Should complete without raising HttpError 429
```

### 3. Production Monitoring

Add logging to track API usage:

```python
api_call_count = 0

def track_api_call(call_type: str):
    global api_call_count
    api_call_count += 1
    logger.info(f"API Call #{api_call_count}: {call_type}")

# At end of update
logger.info(f"Total API calls this update: {api_call_count}")
```

---

## Additional Considerations

### 1. Write Request Optimization

While your current issue is with **read** requests, consider optimizing writes too:

- Use `spreadsheets.values.batchUpdate` to write multiple ranges in one call
- Use `spreadsheets.batchUpdate` to combine formatting operations

Example from your code that could be optimized (sheet_updater.py:700-703):

```python
# CURRENT: 2 write API calls
service.spreadsheets().values().update(...)  # Update G1
service.spreadsheets().values().update(...)  # Update B8

# OPTIMIZED: 1 batch write API call
service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={
        'valueInputOption': 'USER_ENTERED',
        'data': [
            {'range': 'Summary!G1', 'values': [[timestamp]]},
            {'range': 'Summary!B8', 'values': [[readable_timestamp]]}
        ]
    }
).execute()
```

**Good news**: You're already using `batchUpdate` in `update_timestamp()` (line 700)! ✅

### 2. Caching Consideration

For operations that run frequently (e.g., automated GitHub Actions), consider:
- Caching spreadsheet metadata in a local file
- Only re-fetching metadata when necessary
- Trade-off: Added complexity vs. quota savings

### 3. Quota Increase Request

If optimizations aren't sufficient, you can request a quota increase:
- Google Cloud Console → APIs & Services → Quotas
- Select "Sheets API v4" → "Read requests per minute per user"
- Click "Edit Quotas" and request increase
- **Note**: Not guaranteed to be approved

---

## Sources

Research for this document:

- [Google Sheets API Usage Limits - Official Documentation](https://developers.google.com/workspace/sheets/api/limits)
- [Google Sheets API Batch Requests Guide](https://developers.google.com/workspace/sheets/api/guides/batch)
- [Batch Update Method Reference](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate)
- [Batch Get Method Reference](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchUpdate)
- [Google Sheets API Limits Overview - Stateful](https://stateful.com/blog/google-sheets-api-limits)
- [Google API Quota Limits Documentation](https://docs.mobilitystream.com/gsi/google-api-quota-limits)

---

## Conclusion

Your best path forward is:

1. **Immediate**: Implement cache reuse (Solution 2) + exponential backoff (Solution 3)
   - Low effort, immediate stability improvement
   - Prevents crashes while you work on larger optimization

2. **Short-term**: Implement batch reads (Solution 1)
   - Highest impact optimization
   - Reduces API calls by 82%

3. **Monitor**: Add logging to track API usage
   - Verify optimizations are working
   - Identify any remaining bottlenecks

**Estimated Total Effort**: 5-7 hours over 1-2 weeks

**Expected Result**: Go from ~39 reads/update to ~7 reads/update (82% reduction), allowing you to safely run 8+ updates per minute instead of risking limits at 2 updates/minute.
