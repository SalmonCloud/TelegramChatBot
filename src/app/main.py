import asyncio
from app.logging_config import setup_logging
from app.telegram.client import run_bot


def main():
    setup_logging()
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
