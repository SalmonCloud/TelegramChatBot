import asyncio
from src.app.logging_config import setup_logging
from src.app.telegram.client import run_bot


def main():
    setup_logging()
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
