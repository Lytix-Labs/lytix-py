import asyncio

from lytix_py.Lytix.Lytix import lytix
from lytix_py.Lytix.RunTestSuite import runTestSuite


@lytix.test(testsToRun=["No Profanity Test"])
async def test1():
    modelInput = "test1-input"
    modelOutput = "This should pass"
    lytix.setOutput(modelOutput)
    lytix.setInput(modelInput)


@lytix.test(testsToRun=["No Profanity Test"])
def test2():
    modelInput = "test2-input"
    modelOutput = "This should fucking fail"
    lytix.setOutput(modelOutput)
    lytix.setInput(modelInput)


@lytix.test(testsToRun=["No Profanity Test"])
def test3():
    modelInput = "test3-input"
    modelOutput = "You are stupid"
    lytix.setOutput(modelOutput)
    lytix.setInput(modelInput)


async def main():
    await runTestSuite()
    return


if __name__ == "__main__":
    asyncio.run(main())