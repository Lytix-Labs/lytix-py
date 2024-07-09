import asyncio
from lytix_py import lytix


userInput = "Whats the capital of France?"

"""
The function to be traced
"""


@lytix.trace(modelName="nodeCli")
async def getResponse(logger):
    modelOutput = "111Paris is the capital of france1111"

    # Set our defined params however we want
    lytix.setMessage(userInput, "user")
    lytix.setMessage(modelOutput, "assistant")

    # Optional values
    lytix.setUserIdentifier("testUser")
    lytix.setSessionId("testSession")

    return modelOutput


@lytix.trace(modelName="nodeCli")
async def getResponse2(logger):
    modelOutput = "2222Paris is the capital of france2222"

    # Set our defined params however we want
    lytix.setMessage(userInput, "user")
    lytix.setMessage(modelOutput, "assistant")

    # Optional values
    lytix.setUserIdentifier("testUser")
    lytix.setSessionId("testSession")
    lytix.setBackingModel("LLAMA_3_8B_INSTRUCT")

    return modelOutput


async def main():
    response = await getResponse("What is the capital of France?")
    print(response)

    response = await getResponse2("What is the capital of France?")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
