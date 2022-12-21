import asyncio
from aiosupabase.utils import logger
from client import Supabase

async def run_test():
    data = await Supabase.atable("profiles").select("*").execute()
    logger.info(f"Running test: {data}")

    users = await Supabase.auth.async_list_users()
    logger.info(f"Users: {users}")

    logger.info(f"Auth Session: {Supabase.auth.session}")

    # user = await Supabase.auth.async_sign_up(
    #     email = "myuser@test.com",
    #     password = "test1234",
    # )
    # logger.info(f"User: {user}")
    # delete user




asyncio.run(run_test())