"""Pytest configuration and shared test fixtures with isolated test database."""

from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from app.models.cell import Cell
from app.models.division import CellDivisionRecord

# Isolated in-memory SQLite database for test runs
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all schema tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide clean database session wrapped in a transaction rollbacked after test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with get_db dependency overridden to use the isolated test database."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_cell(db_session: Session) -> Cell:
    """Fixture providing a standard test cell sample in the database."""
    cell = Cell(
        id="TEST-CELL-001",
        name="Test Yeast BY4741",
        organism="Saccharomyces cerevisiae",
        cell_type="Budding yeast",
        passage_number=1,
        source_line="Lab WT",
        description="Controlled test specimen",
    )
    db_session.add(cell)
    db_session.commit()
    db_session.refresh(cell)
    return cell
