from sqlalchemy import select

from api.app.database import SessionLocal, engine, get_db
from api.app.models import Service


def test_database_connection() -> None:
    with engine.connect() as connection:
        assert connection is not None


def test_database_session() -> None:
    db = SessionLocal()

    try:
        assert db.is_active
    finally:
        db.close()


def test_get_db_closes_session() -> None:
    generator = get_db()
    db = next(generator)

    assert db.is_active

    generator.close()


def test_service_can_be_persisted() -> None:
    db = SessionLocal()

    try:
        service = Service(
            name="test-service",
            namespace="default",
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        assert service.id is not None

        result = db.execute(
            select(Service).where(Service.name == "test-service")
        )
        saved_service = result.scalar_one()

        assert saved_service.name == "test-service"
        assert saved_service.namespace == "default"

        db.delete(service)
        db.commit()

    finally:
        db.close()