from user_manager import UserManager
import asyncio
import sys
import random

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <database> <username>")
    sys.exit(1)

async def main():
    man = UserManager(sys.argv[1])
    await man.connect()

    if await man.is_username_taken(sys.argv[2]):
        print("Username is taken!")
        await man.shutdown()
        return

    new_token: str = str(random.randint(0, 9999))
    while len(new_token) < 4:
        new_token = "0" + new_token
    while await man.check_token(new_token) is not None:
        new_token: str = str(random.randint(0, 9999))
        while len(new_token) < 4:
            new_token = "0" + new_token

    await man.create_user(sys.argv[2], new_token)
    print(f"User '{sys.argv[2]}' has been created with token: '{new_token}'!")

    await man.shutdown()

asyncio.run(main())
