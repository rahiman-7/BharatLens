import os
import pytest

# Point to an isolated test database BEFORE app imports
TEST_DB_FILE = "test_bharatlens.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_FILE}"

from app.core.config import settings
settings.DATABASE_URL = f"sqlite:///./{TEST_DB_FILE}"

from app.db.database import engine
from app.models import Base
from seed import seed_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure tests run against a clean, isolated database seeded with categories."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield
    # Teardown
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
