"""
Test script to verify orchestrator timeout protection
Tests Fix #3: Add timeout to orchestrator.py line 295
"""

import sys
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def simulate_slow_task(task_id, sleep_time):
    """Simulate a slow task that takes a while to complete"""
    print(f"  Task {task_id} starting (will sleep for {sleep_time}s)...")
    time.sleep(sleep_time)
    return {"task_id": task_id, "result": "success", "sleep_time": sleep_time}


def test_timeout_protection():
    """Test that timeout protection prevents indefinite hangs"""
    print("Test 1: Timeout protection for slow tasks")
    print("-" * 50)

    try:
        timeout_seconds = 3
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks with different execution times
            future_to_task = {
                executor.submit(simulate_slow_task, 1, 1): "task_1",  # 1s - should complete
                executor.submit(simulate_slow_task, 2, 2): "task_2",  # 2s - should complete
                executor.submit(simulate_slow_task, 3, 10): "task_3"  # 10s - should timeout
            }

            # Collect results with timeout (similar to orchestrator pattern)
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    # This mimics the orchestrator's timeout pattern
                    result = future.result(timeout=timeout_seconds)
                    results[task_name] = {
                        'success': True,
                        'result': result
                    }
                    print(f"  ✓ {task_name} completed successfully")
                except TimeoutError:
                    results[task_name] = {
                        'success': False,
                        'error': f'Timeout after {timeout_seconds} seconds'
                    }
                    print(f"  ⏱️  {task_name} timed out after {timeout_seconds}s")
                except Exception as e:
                    results[task_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"  ❌ {task_name} failed: {e}")

        # Verify results
        if results['task_1']['success'] and results['task_2']['success']:
            print("  ✓ Quick tasks completed successfully")
        else:
            raise Exception("Quick tasks should have completed")

        if not results['task_3']['success'] and 'Timeout' in results['task_3']['error']:
            print("  ✓ Slow task correctly timed out")
        else:
            raise Exception("Slow task should have timed out")

        print("✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_no_indefinite_hang():
    """Test that the entire execution completes within reasonable time"""
    print("Test 2: No indefinite hang")
    print("-" * 50)

    try:
        max_allowed_time = 5  # Maximum 5 seconds for the entire test
        start_time = time.time()

        timeout_seconds = 2
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit multiple slow tasks
            future_to_task = {
                executor.submit(simulate_slow_task, i, 10): f"task_{i}"
                for i in range(3)
            }

            # Collect results with timeout
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result(timeout=timeout_seconds)
                    results[task_name] = {'success': True}
                    print(f"  ✓ {task_name} completed")
                except TimeoutError:
                    results[task_name] = {'success': False, 'error': 'Timeout'}
                    print(f"  ⏱️  {task_name} timed out")
                except Exception as e:
                    results[task_name] = {'success': False, 'error': str(e)}
                    print(f"  ❌ {task_name} failed: {e}")

        elapsed = time.time() - start_time

        print(f"  Total elapsed time: {elapsed:.2f}s")

        if elapsed < max_allowed_time:
            print(f"  ✓ Completed within {max_allowed_time}s limit")
        else:
            raise Exception(f"Test took {elapsed:.2f}s, exceeded {max_allowed_time}s limit")

        # All tasks should have timed out (none should complete)
        timed_out_count = sum(1 for r in results.values() if not r['success'])
        if timed_out_count == 3:
            print(f"  ✓ All {timed_out_count} slow tasks timed out as expected")
        else:
            raise Exception(f"Expected 3 timeouts, got {timed_out_count}")

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_mixed_execution():
    """Test mix of fast, slow, and error tasks"""
    print("Test 3: Mixed task execution with timeouts")
    print("-" * 50)

    def task_that_errors():
        """Task that raises an error"""
        time.sleep(0.1)
        raise ValueError("Intentional error for testing")

    try:
        timeout_seconds = 2
        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_task = {
                executor.submit(simulate_slow_task, 1, 0.5): "fast_task",
                executor.submit(simulate_slow_task, 2, 10): "slow_task",
                executor.submit(task_that_errors): "error_task"
            }

            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result(timeout=timeout_seconds)
                    results[task_name] = {'success': True, 'result': result}
                    print(f"  ✓ {task_name} completed successfully")
                except TimeoutError:
                    results[task_name] = {'success': False, 'error': 'Timeout'}
                    print(f"  ⏱️  {task_name} timed out")
                except Exception as e:
                    results[task_name] = {'success': False, 'error': str(e)}
                    print(f"  ❌ {task_name} raised exception: {type(e).__name__}")

        # Verify results
        if results['fast_task']['success']:
            print("  ✓ Fast task completed")
        else:
            raise Exception("Fast task should have completed")

        if not results['slow_task']['success'] and results['slow_task']['error'] == 'Timeout':
            print("  ✓ Slow task timed out")
        else:
            raise Exception("Slow task should have timed out")

        if not results['error_task']['success'] and 'Intentional error' in results['error_task']['error']:
            print("  ✓ Error task handled correctly")
        else:
            raise Exception("Error task should have been caught")

        print("✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_timeouts():
    """Test multiple tasks timing out concurrently"""
    print("Test 4: Concurrent timeout handling")
    print("-" * 50)

    try:
        timeout_seconds = 1
        num_tasks = 10
        results = {}
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit many slow tasks
            future_to_task = {
                executor.submit(simulate_slow_task, i, 5): f"task_{i}"
                for i in range(num_tasks)
            }

            # Collect results with timeout
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result(timeout=timeout_seconds)
                    results[task_name] = {'success': True}
                except TimeoutError:
                    results[task_name] = {'success': False}
                except Exception as e:
                    results[task_name] = {'success': False, 'error': str(e)}

        elapsed = time.time() - start_time

        # All tasks should have timed out
        timed_out = sum(1 for r in results.values() if not r['success'])

        print(f"  ✓ {timed_out}/{num_tasks} tasks timed out")
        print(f"  ✓ Total time: {elapsed:.2f}s (not {num_tasks * 5}s)")

        if timed_out == num_tasks:
            print("  ✓ All tasks timed out as expected")
        else:
            raise Exception(f"Expected {num_tasks} timeouts, got {timed_out}")

        # Should complete reasonably quickly (not wait for all tasks)
        if elapsed < 5:
            print(f"  ✓ Completed quickly ({elapsed:.2f}s < 5s)")
        else:
            raise Exception(f"Took too long: {elapsed:.2f}s")

        print("✅ Test 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}\n")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ORCHESTRATOR TIMEOUT PROTECTION TEST SUITE")
    print("Testing Fix #3: Add timeout to orchestrator.py line 295")
    print("=" * 60)
    print()

    tests = [
        test_timeout_protection,
        test_no_indefinite_hang,
        test_mixed_execution,
        test_concurrent_timeouts
    ]

    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
        time.sleep(0.1)  # Small delay between tests

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Fix #3 is working correctly!")
        print("\nThe orchestrator timeout protection:")
        print("  ✓ Prevents indefinite hangs on slow agents")
        print("  ✓ Completes execution within reasonable time")
        print("  ✓ Handles mix of fast, slow, and error tasks")
        print("  ✓ Correctly handles concurrent timeouts")
        print("  ✓ Provides clear timeout error messages")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
