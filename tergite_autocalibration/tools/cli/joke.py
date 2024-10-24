# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typer

joke_cli = typer.Typer()


@joke_cli.callback()
def joke():
    import asyncio
    from jokeapi import Jokes

    async def print_joke():
        j = await Jokes()  # Initialise the class
        joke_ = await j.get_joke(
            blacklist=["racist", "religious", "political", "nsfw", "sexist"]
        )  # Retrieve a random joke
        if joke_["type"] == "single":  # Print the joke
            print(joke_["joke"])
        else:
            print(joke_["setup"])
            print(joke_["delivery"])

    asyncio.run(print_joke())
