import asyncio
from lytix_py.Lytix.Lytix import lytix, _lytixTraceContext


userInput = "Whats the capital of France?"

"""
The function to be traced
"""


@lytix.trace(modelName="nodeCli")
async def getResponse(logger):
    modelOutput = "111Paris is the capital of france1111"

    # Set our defined params however we want
    lytix.setInput(userInput)
    lytix.setOutput(modelOutput)

    # Optional values
    lytix.setUserIdentifier("testUser")
    lytix.setSessionId("testSession")

    print(f"FirstCall", _lytixTraceContext.get())

    return modelOutput


@lytix.trace(modelName="nodeCli")
async def getResponse2(logger):
    modelOutput = "2222Paris is the capital of france2222"

    # Set our defined params however we want
    lytix.setInput(userInput)
    lytix.setOutput(modelOutput)

    # Optional values
    lytix.setUserIdentifier("testUser")
    lytix.setSessionId("testSession")
    print(f"SecondCall", _lytixTraceContext.get())


async def main():
    response = await getResponse("What is the capital of France?")
    print(response)

    response = await getResponse2("What is the capital of France?")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
