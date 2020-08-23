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

    if not await man.is_username_taken(sys.argv[2]):
        print("User does not exist!")
        await man.shutdown()
        return

    await man.drop_user(sys.argv[2])
    print(f"User '{sys.argv[2]}' has been removed from the database!")

    await man.shutdown()

asyncio.run(main())
