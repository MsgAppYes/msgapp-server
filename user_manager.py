import aiosqlite
from typing import Union


class UserManager:
    def __init__(self, database_name: str):
        self.db_name: str = database_name
        self.connection: aiosqlite.Connection = None

    async def connect(self) -> None:
        self.connection = await aiosqlite.connect(self.db_name)
        await self.connection.execute("CREATE TABLE IF NOT EXISTS Users (Username text, Token text);")
        await self.connection.commit()
    
    async def check_token(self, token: str) -> Union[str, None]:
        async with self.connection.execute("SELECT * FROM Users WHERE Token=?", (token,)) as cursor:
            async for row in cursor:
                return row[0]
            return None

    async def is_username_taken(self, username: str) -> bool:
        async with self.connection.execute("SELECT * FROM Users WHERE Username=?", (username,)) as cursor:
            async for row in cursor:
                return True
            return False

    async def create_user(self, username: str, token: str) -> None:
        await self.connection.execute("INSERT INTO Users VALUES (?,?)", (username, token))
        await self.connection.commit()

    async def drop_user(self, username: str) -> None:
        await self.connection.execute("DELETE FROM Users WHERE Username=?", (username,))
        await self.connection.commit()

    async def shutdown(self) -> None:
        await self.connection.commit()
        await self.connection.close()
