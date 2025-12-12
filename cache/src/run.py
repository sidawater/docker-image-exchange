import os
import asyncio
import uvicorn
from dotenv import load_dotenv
from app import create_app
from init.config.server import init_server_config

load_dotenv()
args = init_server_config()


async def main():
    app = await create_app(debug=args.reload)
    config = uvicorn.Config(
        app,
        host=args.host,
        port=args.port,
        reload=args.debug,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    asyncio.run(main())
