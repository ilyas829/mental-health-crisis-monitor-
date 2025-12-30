import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'
from app.vertex_ai_client import VertexAIClient

async def test():
    client = VertexAIClient()
    response = await client.generate_response("kill me", [])
    print(response)

import asyncio
asyncio.run(test())
