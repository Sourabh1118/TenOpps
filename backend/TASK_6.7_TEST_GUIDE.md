# Task 6.7: Running Property Tests for Deduplication Commutativity

## Quick Start

### Run All Deduplication Property Tests
```bash
cd backend
source venv/bin/activate
pytest tests/test_deduplication_properties.py -v --hypothesis-show-statistics
```

### Run Only Task 6.7 Tests (Commutativity)
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity -v --hypothesis-show-statistics
```

### Run Individual Test Methods

#### Test Similarity Commutativity
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity::test_similarity_commutativity -v
```

#### Test Database Invariant (No Duplicates >= 0.8)
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity::test_no_two_jobs_exceed_similarity_threshold -v
```

#### Test Random Job Pairs Symmetry
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity::test_random_job_pairs_symmetry -v
```

## Test Configuration

### Hypothesis Settings
- `test_similarity_commutativity`: 100 examples
- `test_no_two_jobs_exceed_similarity_threshold`: 50 examples
- `test_random_job_pairs_symmetry`: 50 examples

### Adjust Example Count
To run more examples for thorough testing:
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity -v \
  --hypothesis-max-examples=500
```

### Show Detailed Statistics
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity -v \
  --hypothesis-show-statistics \
  --hypothesis-verbosity=verbose
```

## Understanding Test Output

### Successful Test Run
```
tests/test_deduplication_properties.py::TestDeduplicationCommutativity::test_similarity_commutativity PASSED
tests/test_deduplication_properties.py::TestDeduplicationCommutativity::test_no_two_jobs_exceed_similarity_threshold PASSED
tests/test_deduplication_properties.py::TestDeduplicationCommutativity::test_random_job_pairs_symmetry PASSED
```

### Hypothesis Statistics
After running with `--hypothesis-show-statistics`, you'll see:
- Number of examples tried
- Number of examples filtered (via `assume()`)
- Test execution time
- Shrinking attempts (if failures occur)

### Test Failure Example
If commutativity is violated, you'll see:
```
AssertionError: Commutativity violated: is_duplicate(j1, j2)=True != is_duplicate(j2, j1)=False
```

## Test Properties Validated

### 1. Similarity Commutativity
**Property:** `similarity(j1, j2) == similarity(j2, j1)`

**What it tests:**
- Duplicate detection is symmetric
- Order of comparison doesn't matter
- All match components are commutative

**Requirements:** 2.1, 2.6, 2.10

### 2. Database Invariant
**Property:** No two jobs in database have similarity >= 0.8

**What it tests:**
- Simulates database constraint
- Verifies deduplication prevents duplicates
- Checks all job pairs in a list

**Requirements:** 2.1, 2.6, 2.10

### 3. Random Job Pairs Symmetry
**Property:** Symmetry holds with random thresholds

**What it tests:**
- Symmetry with default thresholds
- Symmetry with custom thresholds
- Consistency across threshold variations

**Requirements:** 2.1, 2.6, 2.10

## Debugging Failed Tests

### Enable Verbose Output
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity -vv
```

### Print Test Examples
Add `--hypothesis-verbosity=verbose` to see generated examples:
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity -v \
  --hypothesis-verbosity=verbose
```

### Reproduce Specific Failure
Hypothesis will print a `@reproduce_failure` decorator when a test fails. Copy it to the test method to reproduce:
```python
@reproduce_failure('6.92.1', b'...')
def test_similarity_commutativity(self, job1, job2):
    ...
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Property Tests
  run: |
    cd backend
    source venv/bin/activate
    pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity \
      -v --hypothesis-show-statistics \
      --junitxml=test-results/junit.xml
```

### Coverage Report
```bash
pytest tests/test_deduplication_properties.py::TestDeduplicationCommutativity \
  --cov=app.services.deduplication \
  --cov-report=html \
  --cov-report=term
```

## Performance Considerations

### Test Execution Time
- Each test method: ~5-30 seconds (depending on examples)
- Full test class: ~1-2 minutes
- With increased examples (500): ~5-10 minutes

### Optimization Tips
1. Use appropriate `max_examples` for CI vs local testing
2. Filter invalid cases early with `assume()`
3. Use `@settings(deadline=None)` for slow operations
4. Profile with `--hypothesis-profile=dev` or `--hypothesis-profile=ci`

## Common Issues

### Issue: Too Many Filtered Examples
**Symptom:** `Unsatisfiable: Unable to satisfy assumptions`

**Solution:** Relax `assume()` constraints or adjust test data generation

### Issue: Flaky Tests
**Symptom:** Tests pass/fail randomly

**Solution:** Check for floating-point comparison issues, use appropriate tolerance

### Issue: Slow Test Execution
**Symptom:** Tests take too long

**Solution:** Reduce `max_examples` or optimize test logic

## Additional Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Pytest Documentation](https://docs.pytest.org/)

## Test Maintenance

### When to Update Tests
- When deduplication algorithm changes
- When similarity thresholds are adjusted
- When new matching stages are added
- When requirements change

### Test Review Checklist
- [ ] Tests validate correct requirements
- [ ] Appropriate number of examples
- [ ] Clear assertion messages
- [ ] Proper use of `assume()`
- [ ] Documentation is up-to-date
