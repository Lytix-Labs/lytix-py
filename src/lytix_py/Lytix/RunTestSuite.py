import asyncio
import multiprocessing
import os
import sys
import threading
import time
import uuid
from lytix_py.Lytix.LytixTest import lytixTest
from lytix_py.MetricCollector.MetricCollector import MetricCollector
from lytix_py.colors import colors


def printTestRunning():
    while True:
        print(f"{colors.YELLOW}🐶 Waiting for Lytix Response...{colors.RESET}")
        time.sleep(2.5)


async def runTestSuite():
    """
    Gather all @lytix.test decorators present and
    run the test suite
    """
    allTests = lytixTest._testState

    print(
        f"{colors.GREEN}Starting test suite for: {len(allTests)} test(s)...{colors.RESET}"
    )

    """
    First create a test suite
    """
    testSuiteId = MetricCollector._createTestSuite()

    """
    Then all each function
    """
    asyncFunctions = []
    syncFunctions = []
    for func in allTests.values():
        if asyncio.iscoroutinefunction(func["function"]):
            asyncFunctions.append(func)
        else:
            syncFunctions.append(func)

    """
    Keep track of which ones passed and failed so we can report at the end"""
    testsPassed = {}
    testsFailed = {}
    totalTests = len(asyncFunctions) + len(syncFunctions)

    # testRunning = True

    printThread = multiprocessing.Process(target=printTestRunning, args=())
    printThread.start()

    # bLoop = asyncio.new_event_loop()
    # bLoop.run_until_complete(printTestRunning())

    # backgroundPrint = asyncio.create_task(printTestRunning())
    # backgroundPrint = loop.run_coroutine_threadsafe(printTestRunning(), loop)

    # printTask = asyncio.ensure_future(printTestRunning())

    """
    Gather and run the async tests if possible
    """
    for func in asyncFunctions:
        functionName = func["function"].__name__

        @lytixTest.test(
            **func["testArgs"], _testSuiteId=testSuiteId, _testName=functionName
        )
        async def wrapper(*args, **kwargs):
            results = await func["function"](*args, **kwargs)
            return results

        testResult = await wrapper()
        if testResult == "FAILED":
            testsFailed[functionName] = testResult
            print(f"{colors.RED}Test failed for {functionName}{colors.RESET}")
        elif testResult == "SUCCESS":
            testsPassed[functionName] = testResult
            print(f"{colors.GREEN}Test passed for {functionName}{colors.RESET}")
        else:
            print(
                f"{colors.YELLOW}Test result is {testResult} for {functionName} which is unhandled{colors.RESET}"
            )

    """
    Then run all the sync tests one by one
    """
    for func in syncFunctions:
        functionName = func["function"].__name__

        @lytixTest.test(
            **func["testArgs"], _testSuiteId=testSuiteId, _testName=functionName
        )
        def wrapper(*args, **kwargs):
            return func["function"](*args, **kwargs)

        testResult = wrapper()
        if testResult == "FAILED":
            testsFailed[functionName] = testResult
            print(f"{colors.RED}Test failed for {functionName}{colors.RESET}")
        elif testResult == "SUCCESS":
            testsPassed[functionName] = testResult
            print(f"{colors.GREEN}Test passed for {functionName}{colors.RESET}")
        else:
            print(
                f"{colors.YELLOW}Test result is {testResult} for {functionName} which is unhandled{colors.RESET}"
            )

    """
    Report the final results
    """
    printThread.terminate()
    finalizeRes = MetricCollector._finalizeTestGroup(testSuiteId)
    if finalizeRes["valid"] is not True:
        print(
            f"{colors.RED}Failed to finalize test group {testSuiteId} with error: {finalizeRes['error']}{colors.RESET}"
        )
    # testRunning = False
    # backgroundPrint.cancel()
    if len(testsFailed) == 0:
        # All passed
        print(
            f"{colors.GREEN}{len(testsPassed)}/{totalTests} tests passed! 🍾{colors.RESET}"
        )
    else:
        # Some failed
        print(
            f"{colors.RED}{len(testsPassed)}/{totalTests} tests passed!{colors.RESET}"
        )

    for test in testsPassed:
        print(f"{colors.GREEN}-> {test}: passed ✅{colors.RESET}")
    for test in testsFailed:
        print(f"{colors.RED}-> {test}: failed ❌{colors.RESET}")

    if len(testsFailed) > 0:
        sys.exit(1)
