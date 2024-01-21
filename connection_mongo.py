import os
from config import MONGODB_URL
import motor.motor_asyncio


client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)

database = client.tg_bot_scam
