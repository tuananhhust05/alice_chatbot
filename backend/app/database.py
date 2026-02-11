from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.conversations.create_index("user_id")
    await db.conversations.create_index("created_at")
    await db.files.create_index("user_id")
    
    # IP tracking indexes
    await db.ip_messages.create_index("client_ip")
    await db.ip_messages.create_index("user_id")
    await db.ip_messages.create_index("timestamp")
    await db.ip_messages.create_index("conversation_id")
    # Compound index for efficient filtering
    await db.ip_messages.create_index([("client_ip", 1), ("timestamp", -1)])
    await db.ip_messages.create_index([("user_id", 1), ("timestamp", -1)])

    print("Connected to MongoDB")


async def close_db():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_db():
    return db
