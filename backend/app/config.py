import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://tracker:tracker@localhost:5432/tracker",
)
OPENSKY_POLL_SECONDS = float(os.getenv("OPENSKY_POLL_SECONDS", "10"))
POSITION_RETENTION_HOURS = int(os.getenv("POSITION_RETENTION_HOURS", "24"))
OPENSKY_STATES_URL = os.getenv(
    "OPENSKY_STATES_URL",
    "https://opensky-network.org/api/states/all",
)
