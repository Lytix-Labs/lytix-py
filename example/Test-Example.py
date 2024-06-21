import asyncio

from lytix_py.Lytix.LytixTest import lytixTest
from lytix_py.Lytix.RunTestSuite import runTestSuite


@lytixTest.test(testsToRun=["No Profanity Test"])
async def test1():
    modelInput = "test1-input"
    modelOutput = "This should pass"
    lytixTest.setMessage(modelOutput, "user")
    lytixTest.setMessage(modelInput, "assistant")


@lytixTest.test(testsToRun=["No Profanity Test"])
def test2():
    modelInput = "test2-input"
    modelOutput = "Shit, This should fail"
    lytixTest.setMessage(modelOutput, "user")
    lytixTest.setMessage(modelInput, "assistant")


@lytixTest.test(testsToRun=["No Profanity Test"])
def test3():
    modelInput = "test3-input"
    modelOutput = "You are stupid, but this should pass"
    lytixTest.setMessage(modelOutput, "user")
    lytixTest.setMessage(modelInput, "assistant")


async def main():
    await runTestSuite()
    return


if __name__ == "__main__":
    asyncio.run(main())
