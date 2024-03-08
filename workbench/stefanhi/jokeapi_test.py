import asyncio

from jokeapi import Jokes  # Import the Jokes class


async def print_joke():
    j = await Jokes()  # Initialise the class
    joke = await j.get_joke()  # Retrieve a random joke
    if joke["type"] == "single":  # Print the joke
        print(joke["joke"])
    else:
        print(joke["setup"])
        print(joke["delivery"])


asyncio.run(print_joke())
