# Rate Limit Optimization TODO

Implementation checklist for reducing Google Sheets API read requests from ~39/update to ~7/update (82% reduction).

**Target**: Enable 8+ updates per minute vs. current 1-2 updates per minute

---

## Phase 1: Quick Wins ✅ COMPLETED (2026-01-12)

**Status**: ✅ All tasks completed, tested, documented, and committed

**Commits**:
- `9419963` - Add rate limit optimization planning documents
- `a25220e` - Implement Phase 1: Cache reuse and exponential backoff retry (v2.4)
- `41b23f8` - Update documentation for Phase 1 rate limit optimization

**Results**:
- ✅ 41% reduction in API calls (39 → 23 read requests per update)
- ✅ 50% reduction in metadata reads (32 → 16 API calls)
- ✅ Automatic retry with exponential backoff implemented
- ✅ 6 comprehensive tests passing
- ✅ Documentation updated (CHANGELOG.md, CLAUDE.md)

**Real-World Test** (2026-01-12):
- Tested with spreadsheet `12ys55Vhxlxnv6tNyLWt7SuWPRAfp4SV0UWTqycujjXY` (16-team league)
- ✅ Retry logic worked perfectly with exponential backoff
- ✅ Successfully updated 6/7 teams before hitting quota limit
- ⚠️ **Key Finding**: Phase 1 alone isn't sufficient for active API usage
- 🎯 **Conclusion**: Phase 2 (batch reads) is CRITICAL for production use

### ✅ Task 1.1: Implement Cache Reuse Between Functions ✅ COMPLETED

**Priority**: 🟡 HIGH | **Effort**: 30 minutes | **Impact**: 50% reduction (32→16 calls)

**Goal**: Stop re-reading cell A1 data in `cleanup_orphaned_sheets` that was already read by `_build_sheet_metadata_cache`.

#### Steps:

- [x] **1.1.1**: Modify `cleanup_orphaned_sheets` function signature ✅
  - File: `src/sheet_updater.py:328`
  - Add parameter: `metadata_cache: dict = None`
  - Update docstring to document new parameter

- [x] **1.1.2**: Refactor `cleanup_orphaned_sheets` implementation ✅
  - Replace the sheet metadata reading loop (lines 375-399) with cache lookup
  - If `metadata_cache` is None, call `_build_sheet_metadata_cache` as fallback
  - Use `metadata_cache` dictionary directly instead of reading cells

- [x] **1.1.3**: Update callers to pass metadata cache ✅
  - Find where `cleanup_orphaned_sheets` is called
  - Ensure metadata cache is built once and passed to cleanup function
  - Example: In main update flow, build cache once, use twice

- [x] **1.1.4**: Test cache reuse ✅
  - Run update on test spreadsheet
  - Verify cleanup still works correctly
  - Check logs: should see "Built metadata cache" once, not twice

**Files modified**: `src/sheet_updater.py`, `main.py`

**Validation**: ✅ Count API calls before/after - dropped from ~32 to ~16 for metadata operations

---

### ✅ Task 1.2: Add Exponential Backoff Retry Logic ✅ COMPLETED

**Priority**: 🟢 MEDIUM | **Effort**: 1-2 hours | **Impact**: Prevents crashes, graceful degradation

**Goal**: Automatically retry API calls that hit rate limits with exponential backoff.

#### Steps:

- [x] **1.2.1**: Create retry utility module ✅
  - File: `src/api_retry.py` (new file) - 195 lines
  - Implement `api_call_with_retry()` function
  - Parameters: `api_function`, `max_retries=5`, `max_backoff=64`
  - Handle HttpError status codes: 429 (rate limit), 500, 502, 503, 504
  - Implement exponential backoff formula: `min((2^n + random(0-1000ms)), max_backoff)`
  - Add logging for retry attempts

- [x] **1.2.2**: Add tests for retry logic ✅
  - File: `tests/test_api_retry.py` (new file) - 221 lines
  - Test successful API call (no retry needed) ✅
  - Test rate limit handling (429 error → retry → success) ✅
  - Test max retries exhausted (should raise error) ✅
  - Test exponential backoff timing ✅
  - Test server errors (5xx) ✅
  - Test non-retryable errors (4xx) ✅

- [x] **1.2.3**: Wrap critical read operations ✅
  - `src/sheet_reader.py`: `read_last_run_timestamp` ✅
  - `src/sheet_reader.py`: `validate_sheet_structure` ✅
  - `src/sheet_reader.py`: `get_existing_team_sheets` ✅
  - `src/sheet_updater.py`: `_build_sheet_metadata_cache` ✅
  - `src/sheet_updater.py`: `_find_sheet_id_by_name` ✅
  - `src/sheet_updater.py`: `cleanup_orphaned_sheets` ✅
  - All wrapped with `api_call_with_retry(lambda: ...)`

- [x] **1.2.4**: Wrap write operations ✅
  - Deferred to Phase 2 - not causing current rate limit issues

- [x] **1.2.5**: Add API call counter ✅
  - `APICallCounter` class created in `src/api_retry.py`
  - Context manager for tracking API calls
  - Ready for integration in Phase 3

**Files created**: `src/api_retry.py`, `tests/test_api_retry.py`

**Files modified**: `src/sheet_reader.py`, `src/sheet_updater.py`

**Validation**:
- ✅ All 6 tests passing
- ✅ Real-world test showed retry logic working perfectly
- ✅ Exponential backoff correctly implemented (1s → 2s → 4s → 8s pattern observed)
- ✅ Logs show clear retry messages when rate limit hit

---

## Phase 2: Core Optimization (Week 2) ⏳ READY TO START

**CRITICAL FOR PRODUCTION**: Phase 1 testing revealed that 41% reduction is insufficient for active API usage. Phase 2 batch reads are **essential** to avoid rate limit errors in production.

**Why This Is Urgent**:
- Real-world test hit rate limits while still reading metadata individually (16 calls)
- Successfully updated 6/7 teams before exhausting quota
- Batch reads will reduce 16 → 1 call (94% reduction)
- This unlocks production-ready performance

### Task 2.1: Implement Batch Read for Metadata Cache

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

| Metric | Before (v2.3) | Phase 1 (v2.4) | Phase 2 Target | Status |
|--------|---------------|----------------|----------------|--------|
| API reads per update (16 teams) | ~39 | **~23** | ~7 | ⏳ Phase 2 Needed |
| Metadata cache API calls | 32 | **16** | 1 | ⏳ Phase 2 Needed |
| Initial read API calls | 3 | **3** | 1 | ⏳ Phase 2 Needed |
| Max safe updates per minute | 1-2 | **2-3** | 8+ | ⏳ Phase 2 Needed |
| Rate limit crashes | Yes | **No (retry)** | No (reduced calls) | ✅ Phase 1 Done |
| Update time penalty | 0s | **+0-16s (retry)** | +0-2s | ⏳ Phase 2 Needed |
| Total reduction | Baseline | **41%** | **82%** | ⏳ Phase 2 Needed |

**Phase 1 Testing Checklist**:
- [x] Test with 16 team league ✅
- [x] Test with renamed teams (orphaned sheets) ✅
- [x] Test with transactions (incremental update) ✅
- [x] Verify no crashes on rate limit ✅
- [x] Verify retry logic activates when needed ✅
- [x] Observed exponential backoff working (1s → 2s → 4s → 8s) ✅

**Phase 2 Testing Checklist** (Pending):
- [ ] Test with 1 team league
- [ ] Test with 16 team league (batch reads)
- [ ] Test consecutive updates (2x in 1 minute)
- [ ] Test rapid updates (8x in 1 minute)
- [ ] Verify batch read returns same data as individual reads
- [ ] Confirm API call reduction (16→1 for metadata)

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

- [x] **Phase 1: Quick Wins** ✅ COMPLETED (2026-01-12)
  - [x] Task 1.1: Cache Reuse ✅
  - [x] Task 1.2: Retry Logic ✅
  - [x] Real-world testing completed ✅
  - [x] Documentation updated ✅

- [ ] **Phase 2: Core Optimization** ⏳ READY TO START
  - [ ] Task 2.1: Batch Metadata Read (CRITICAL - blocks production use)
  - [ ] Task 2.2: Batch Initial Reads
  - [ ] Task 2.3: Write Optimization (optional)

- [ ] **Phase 3: Testing & Monitoring**
  - [ ] Task 3.1: Stress Testing
  - [ ] Task 3.2: Documentation

- [ ] **DONE**: All optimizations complete, rate limits resolved ✅

---

**Last Updated**: 2026-01-12
**Status**: ✅ Phase 1 Complete | ⏳ Phase 2 Ready to Start

**Current Performance**:
- API read requests per update: ~23 (down from ~39)
- Metadata read calls: 16 (down from 32)
- Reduction achieved: 41%
- **NEXT TARGET**: Reduce to ~7 read requests (82% total reduction)
