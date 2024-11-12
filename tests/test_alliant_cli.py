#!/usr/bin/env python3
"""Command line test script for Alliant Energy API client."""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the custom_components directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "custom_components"))

from alliant_energy.client import AlliantEnergyClient, AlliantEnergyData
from getpass import getpass
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

async def main():
    """Run the test."""
    # Load credentials from .env file if available
    load_dotenv()

    # Get credentials from environment or prompt
    username = os.getenv("ALLIANT_USERNAME")
    if not username:
        username = input("Alliant Energy username: ")

    password = os.getenv("ALLIANT_PASSWORD")
    if not password:
        password = getpass("Alliant Energy password: ")

    client = AlliantEnergyClient(username, password)
    try:
        data = await client.get_data()
        print("\nRetrieved Data:")
        print("-" * 50)
        print(data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
