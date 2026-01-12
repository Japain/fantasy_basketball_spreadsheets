# Rate Limit Optimization TODO

Implementation checklist for reducing Google Sheets API read requests from ~39/update to ~7/update (82% reduction).

**Target**: Enable 8+ updates per minute vs. current 1-2 updates per minute

---

## Phase 1: Quick Wins (Week 1)

### ✅ Task 1.1: Implement Cache Reuse Between Functions

**Priority**: 🟡 HIGH | **Effort**: 30 minutes | **Impact**: 50% reduction (32→16 calls)

**Goal**: Stop re-reading cell A1 data in `cleanup_orphaned_sheets` that was already read by `_build_sheet_metadata_cache`.

#### Steps:

- [ ] **1.1.1**: Modify `cleanup_orphaned_sheets` function signature
  - File: `src/sheet_updater.py:328`
  - Add parameter: `metadata_cache: dict = None`
  - Update docstring to document new parameter

- [ ] **1.1.2**: Refactor `cleanup_orphaned_sheets` implementation
  - Replace the sheet metadata reading loop (lines 375-399) with cache lookup
  - If `metadata_cache` is None, call `_build_sheet_metadata_cache` as fallback
  - Use `metadata_cache` dictionary directly instead of reading cells

- [ ] **1.1.3**: Update callers to pass metadata cache
  - Find where `cleanup_orphaned_sheets` is called
  - Ensure metadata cache is built once and passed to cleanup function
  - Example: In main update flow, build cache once, use twice

- [ ] **1.1.4**: Test cache reuse
  - Run update on test spreadsheet
  - Verify cleanup still works correctly
  - Check logs: should see "Built metadata cache" once, not twice

**Files to modify**: `src/sheet_updater.py`

**Validation**: Count API calls before/after - should drop from ~32 to ~16 for metadata operations

---

### ✅ Task 1.2: Add Exponential Backoff Retry Logic

**Priority**: 🟢 MEDIUM | **Effort**: 1-2 hours | **Impact**: Prevents crashes, graceful degradation

**Goal**: Automatically retry API calls that hit rate limits with exponential backoff.

#### Steps:

- [ ] **1.2.1**: Create retry utility module
  - File: `src/api_retry.py` (new file)
  - Implement `api_call_with_retry()` function
  - Parameters: `api_function`, `max_retries=5`, `max_backoff=64`
  - Handle HttpError status codes: 429 (rate limit), 500, 502, 503, 504
  - Implement exponential backoff formula: `min((2^n + random(0-1000ms)), max_backoff)`
  - Add logging for retry attempts

- [ ] **1.2.2**: Add tests for retry logic
  - File: `tests/test_api_retry.py` (new file)
  - Test successful API call (no retry needed)
  - Test rate limit handling (429 error → retry → success)
  - Test max retries exhausted (should raise error)
  - Test exponential backoff timing

- [ ] **1.2.3**: Wrap critical read operations
  - Identify high-frequency read operations in codebase:
    - `src/sheet_reader.py`: `read_last_run_timestamp` (line 152)
    - `src/sheet_reader.py`: `validate_sheet_structure` (line 212)
    - `src/sheet_updater.py`: `_build_sheet_metadata_cache` (line 114, 267)
    - `src/sheet_updater.py`: `_find_sheet_id_by_name` (line 53)
  - Wrap `.execute()` calls with `api_call_with_retry(lambda: ...)`

- [ ] **1.2.4**: Wrap write operations (optional but recommended)
  - `src/sheet_updater.py`: Clear and update operations
  - `src/sheet_generator.py`: Create and format operations

- [ ] **1.2.5**: Add API call counter (for monitoring)
  - Add global or context-managed counter for API calls
  - Log total API calls at end of update
  - Helps verify optimization effectiveness

**Files to create**: `src/api_retry.py`, `tests/test_api_retry.py`

**Files to modify**: `src/sheet_reader.py`, `src/sheet_updater.py`, `src/sheet_generator.py`

**Validation**:
- Run test suite - all tests should pass
- Simulate rate limit (make 70+ rapid calls) - should complete without crash
- Check logs - should see retry messages when rate limit hit

---

## Phase 2: Core Optimization (Week 2)

### ✅ Task 2.1: Implement Batch Read for Metadata Cache

**Priority**: 🔴 CRITICAL | **Effort**: 3-4 hours | **Impact**: 94% reduction (16→1 call) for metadata

**Goal**: Replace 16+ individual `values().get()` calls with single `values().batchGet()` call.

#### Steps:

- [ ] **2.1.1**: Create new batch read function
  - File: `src/sheet_updater.py:75`
  - Rename existing `_build_sheet_metadata_cache` to `_build_sheet_metadata_cache_legacy`
  - Create new `_build_sheet_metadata_cache` using batch read approach
  - Steps:
    1. Get all sheets with `spreadsheets().get()`
    2. Build list of ranges: `[f"'{sheet_title}'!A1" for sheet_title in ...]`
    3. Call `spreadsheets().values().batchGet(ranges=ranges)` - SINGLE API CALL
    4. Parse `valueRanges` array from response
    5. Build metadata_cache dictionary same as before

- [ ] **2.1.2**: Handle edge cases in batch read
  - Empty sheets (no data in A1)
  - Sheets with invalid team_id format
  - API errors (fall back to legacy method or raise)
  - Single sheet (batch still works, but ensure no regression)

- [ ] **2.1.3**: Update migration function to use batch read
  - File: `src/sheet_updater.py:266`
  - `_migrate_sheet_to_id_based` currently reads existing data
  - Consider if batch read could help here (probably not, single sheet operation)

- [ ] **2.1.4**: Test batch read metadata cache
  - File: `tests/test_sheet_updater.py` (new or existing)
  - Test with 1 sheet, 5 sheets, 16 sheets
  - Compare results: legacy method vs. batch method (should be identical)
  - Verify team_id extraction works correctly
  - Check API call count: should be 1 regardless of sheet count

**Files to modify**: `src/sheet_updater.py`

**Files to create/update**: `tests/test_sheet_updater.py`

**Validation**:
- Unit test comparing legacy vs. batch (results should match)
- Integration test with real spreadsheet
- Check logs: "Built metadata cache with N entries using 1 API call"

---

### ✅ Task 2.2: Implement Batch Read for Initial Reads

**Priority**: 🔴 CRITICAL | **Effort**: 1-2 hours | **Impact**: Combine 2-3 reads into 1

**Goal**: Combine timestamp read + validation reads into single batch call.

#### Steps:

- [ ] **2.2.1**: Create combined initial read function
  - File: `src/sheet_reader.py` (new function)
  - Function: `batch_read_initial_data(service, spreadsheet_id) -> dict`
  - Batch read ranges:
    - `Summary!G1` (timestamp)
    - `Summary!A1:A10` (for validation)
  - Return dict with parsed results: `{'timestamp': ..., 'has_summary': bool}`

- [ ] **2.2.2**: Refactor main update flow
  - File: `main.py` or wherever update workflow is orchestrated
  - Replace separate calls to:
    - `read_last_run_timestamp()`
    - `validate_sheet_structure()`
  - With single call to: `batch_read_initial_data()`
  - Parse results and continue with existing logic

- [ ] **2.2.3**: Keep original functions for backwards compatibility
  - Don't delete `read_last_run_timestamp()` and `validate_sheet_structure()`
  - Mark as deprecated or keep for specific use cases
  - Update documentation

- [ ] **2.2.4**: Test combined initial read
  - Test with new spreadsheet (no timestamp)
  - Test with existing spreadsheet (has timestamp)
  - Test with invalid spreadsheet (no Summary sheet)
  - Verify same behavior as separate calls

**Files to modify**: `src/sheet_reader.py`, `main.py`

**Validation**:
- Integration test comparing separate vs. batch approach
- Verify timestamp parsing still works
- Check logs: should see 1 API call instead of 2-3

---

### ✅ Task 2.3: Optimize Write Operations (Bonus)

**Priority**: 🟢 LOW | **Effort**: 1 hour | **Impact**: Reduce write API calls

**Goal**: While not causing current rate limit issues, optimize writes for future-proofing.

#### Steps:

- [ ] **2.3.1**: Audit current write operations
  - Check `src/sheet_updater.py` for multiple sequential writes
  - Check `src/sheet_generator.py` for opportunities to batch
  - Already using `batchUpdate` in `update_timestamp()` ✅ (line 700)

- [ ] **2.3.2**: Combine clear + write operations
  - Currently: clear range, then write range (2 API calls)
  - Consider: Can we write new data directly without clearing? (depends on size)
  - Or: Use batch write to clear + write in one call

- [ ] **2.3.3**: Batch formatting requests
  - Review `_create_team_sheet_formatting()` - already batches! ✅
  - Review `create_summary_sheet()` - already batches! ✅
  - Good news: formatting is already optimized

**Files to review**: `src/sheet_updater.py`, `src/sheet_generator.py`

**Validation**: Count write API calls before/after optimization

---

## Phase 3: Testing & Monitoring

### ✅ Task 3.1: Create Rate Limit Stress Test

**Priority**: 🟡 HIGH | **Effort**: 1 hour

#### Steps:

- [ ] **3.1.1**: Create stress test script
  - File: `tests/test_rate_limits.py` (new file)
  - Make 70 rapid API calls (exceeds 60/minute limit)
  - Should complete successfully with retry logic
  - Should NOT crash with 429 error

- [ ] **3.1.2**: Add API call tracking
  - Implement counter/logger to track all API calls during update
  - Log total at end: "Total API calls: 7 (Target: <10)"
  - Compare before/after optimization

- [ ] **3.1.3**: Create benchmark script
  - File: `benchmark_api_calls.py` (new file)
  - Run update on test spreadsheet
  - Count and categorize API calls:
    - Read requests: X
    - Write requests: Y
    - Batch operations: Z
  - Print summary report

**Files to create**: `tests/test_rate_limits.py`, `benchmark_api_calls.py`

---

### ✅ Task 3.2: Update Documentation

**Priority**: 🟢 MEDIUM | **Effort**: 30 minutes

#### Steps:

- [ ] **3.2.1**: Update CLAUDE.md
  - Add section on rate limit optimizations
  - Document batch read approach
  - Explain retry logic

- [ ] **3.2.2**: Add inline code comments
  - Document why batch reads are used
  - Explain cache reuse pattern
  - Note rate limit considerations

- [ ] **3.2.3**: Update README (if exists)
  - Mention rate limit handling
  - Document expected API usage (~7 calls/update)

**Files to modify**: `CLAUDE.md`, `README.md`, code files with comments

---

## Success Metrics

Track these metrics before and after optimization:

| Metric | Before | After (Target) | Status |
|--------|--------|----------------|--------|
| API reads per update (16 teams) | ~39 | ~7 | ⏳ Pending |
| Metadata cache API calls | 32 | 1 | ⏳ Pending |
| Initial read API calls | 3 | 1 | ⏳ Pending |
| Max safe updates per minute | 1-2 | 8+ | ⏳ Pending |
| Rate limit crashes | Yes | No | ⏳ Pending |
| Update time penalty | 0s | +0-2s | ⏳ Pending |

**Testing Checklist**:
- [ ] Test with 1 team league
- [ ] Test with 16 team league
- [ ] Test with renamed teams (orphaned sheets)
- [ ] Test with new teams (sheet creation)
- [ ] Test consecutive updates (2x in 1 minute)
- [ ] Test rapid updates (8x in 1 minute)
- [ ] Verify no crashes on rate limit
- [ ] Verify retry logic activates when needed

---

## Implementation Notes

### Code Review Checklist

Before merging each phase:
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] API call counts logged and verified
- [ ] Error handling covers edge cases
- [ ] Code follows existing style/patterns
- [ ] Documentation updated

### Rollback Plan

If optimization causes issues:
- Keep `_build_sheet_metadata_cache_legacy` as fallback
- Add feature flag to toggle batch vs. individual reads
- Monitor logs for errors after deployment

### GitHub Actions Considerations

If running via GitHub Actions:
- Verify retry logic works in CI environment
- Consider longer timeouts for retries
- Test with GitHub Actions secrets/credentials

---

## Timeline

**Week 1** (Phase 1): Cache reuse + retry logic
- Day 1-2: Task 1.1 (Cache reuse)
- Day 3-5: Task 1.2 (Retry logic + testing)

**Week 2** (Phase 2): Batch read optimization
- Day 1-3: Task 2.1 (Batch metadata read)
- Day 4: Task 2.2 (Batch initial reads)
- Day 5: Task 2.3 (Write optimization - optional)

**Week 3** (Phase 3): Testing & polish
- Day 1-2: Task 3.1 (Stress testing)
- Day 3: Task 3.2 (Documentation)
- Day 4-5: Buffer for fixes/adjustments

**Total Effort**: ~12-15 hours over 3 weeks

---

## Quick Reference: Files to Modify

### New Files to Create:
- [ ] `src/api_retry.py` - Exponential backoff retry utility
- [ ] `tests/test_api_retry.py` - Tests for retry logic
- [ ] `tests/test_rate_limits.py` - Rate limit stress tests
- [ ] `tests/test_sheet_updater.py` - Batch read tests (if not exists)
- [ ] `benchmark_api_calls.py` - API call tracking script

### Existing Files to Modify:
- [ ] `src/sheet_updater.py` - Batch reads, cache reuse, retry wrapper
- [ ] `src/sheet_reader.py` - Batch initial reads, retry wrapper
- [ ] `src/sheet_generator.py` - Retry wrapper (optional)
- [ ] `main.py` - Update workflow to use batch reads
- [ ] `CLAUDE.md` - Documentation updates

---

## Questions / Blockers

Track any questions or blockers here:

- [ ] Q: Should we add retry logic to write operations too?
  - A: Recommended, but not critical since writes aren't causing current rate limit issue

- [ ] Q: What max_retries value should we use?
  - A: Start with 5, adjust based on testing. Google recommends 5-10.

- [ ] Q: Should we cache metadata to disk to reduce reads further?
  - A: Not necessary for now. Revisit if still hitting limits after optimization.

- [ ] Q: Do we need to update CI/CD scripts?
  - A: Likely no changes needed, but test GitHub Actions workflow after changes.

---

## Completion Status

- [ ] Phase 1: Quick Wins
  - [ ] Task 1.1: Cache Reuse
  - [ ] Task 1.2: Retry Logic

- [ ] Phase 2: Core Optimization
  - [ ] Task 2.1: Batch Metadata Read
  - [ ] Task 2.2: Batch Initial Reads
  - [ ] Task 2.3: Write Optimization (optional)

- [ ] Phase 3: Testing & Monitoring
  - [ ] Task 3.1: Stress Testing
  - [ ] Task 3.2: Documentation

- [ ] **DONE**: All optimizations complete, rate limits resolved ✅

---

**Last Updated**: 2026-01-12
**Status**: Ready to start Phase 1
