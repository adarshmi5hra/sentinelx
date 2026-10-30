from uuid import uuid4

from datetime import timedelta
from api.app.models import utc_now

from sqlalchemy import select

from api.app.database import SessionLocal, engine, get_db
from api.app.models import (
    Service,
    Incident,
    IncidentEvent,
    Metric,
    Anomaly,
    Prediction,
    RemediationAction,
    AuditLog,
)


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
    service = Service(
        name=f"test-service-{uuid4().hex}",
        namespace="default",
    )

    try:
        db.add(service)
        db.commit()
        db.refresh(service)

        assert service.id is not None

        result = db.execute(select(Service).where(Service.name == service.name))
        saved_service = result.scalar_one()

        assert saved_service.name == service.name
        assert saved_service.namespace == "default"

    finally:
        try:
            db.rollback()

            if service.id is not None:
                db.delete(service)
                db.commit()
        finally:
            db.close()


def test_incident_and_event_can_be_persisted() -> None:
    db = SessionLocal()
    service = Service(
        name=f"test-incident-{uuid4().hex}",
        namespace="default",
    )

    try:
        db.add(service)
        db.commit()
        db.refresh(service)

        incident = Incident(
            service_id=service.id,
            severity="high",
            probable_cause="Sustained high CPU usage",
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        event = IncidentEvent(
            incident_id=incident.id,
            event_type="anomaly_detected",
            evidence={
                "metric": "cpu_usage",
                "value": 96.5,
                "threshold": 85,
            },
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        saved_incident = db.get(Incident, incident.id)
        saved_event = db.get(IncidentEvent, event.id)

        assert saved_incident is not None
        assert saved_incident.severity == "high"
        assert saved_incident.status == "open"

        assert saved_event is not None
        assert saved_event.event_type == "anomaly_detected"
        assert saved_event.evidence["value"] == 96.5

    finally:
        try:
            db.rollback()

            if service.id is not None:
                # Incidents must be deleted before the service.
                incidents = db.scalars(
                    select(Incident).where(Incident.service_id == service.id)
                ).all()

                for incident in incidents:
                    db.delete(incident)

                db.commit()
                db.delete(service)
                db.commit()
        finally:
            db.close()


def test_metric_can_be_persisted() -> None:
    db = SessionLocal()
    service = Service(
        name=f"test-metric-{uuid4().hex}",
        namespace="default",
    )

    try:
        db.add(service)
        db.commit()
        db.refresh(service)

        metric = Metric(
            service_id=service.id,
            metric="cpu_usage",
            value=96.5,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)

        saved_metric = db.get(Metric, metric.id)

        assert saved_metric is not None
        assert saved_metric.service_id == service.id
        assert saved_metric.metric == "cpu_usage"
        assert saved_metric.value == 96.5
        assert saved_metric.timestamp is not None

    finally:
        try:
            db.rollback()

            if service.id is not None:
                # The database cascades deletion to the metric.
                db.delete(service)
                db.commit()
        finally:
            db.close()


def test_anomaly_can_be_persisted() -> None:
    db = SessionLocal()
    service = Service(
        name=f"test-anomaly-{uuid4().hex}",
        namespace="default",
    )

    try:
        db.add(service)
        db.commit()
        db.refresh(service)

        anomaly = Anomaly(
            service_id=service.id,
            metric="cpu_usage",
            score=3.8,
            severity="high",
        )
        db.add(anomaly)
        db.commit()
        db.refresh(anomaly)

        saved_anomaly = db.get(Anomaly, anomaly.id)

        assert saved_anomaly is not None
        assert saved_anomaly.service_id == service.id
        assert saved_anomaly.metric == "cpu_usage"
        assert saved_anomaly.score == 3.8
        assert saved_anomaly.severity == "high"

    finally:
        try:
            db.rollback()

            if service.id is not None:
                # The database cascades deletion to the anomaly.
                db.delete(service)
                db.commit()
        finally:
            db.close()


def test_prediction_can_be_persisted() -> None:
    db = SessionLocal()
    service = Service(
        name=f"test-prediction-{uuid4().hex}",
        namespace="default",
    )

    try:
        db.add(service)
        db.commit()
        db.refresh(service)

        prediction = Prediction(
            service_id=service.id,
            metric="cpu_usage",
            predicted_value=92.5,
            target_timestamp=utc_now() + timedelta(minutes=10),
            horizon_seconds=600,
            confidence_score=0.95,
            model_name="isolation-forest",
            details={"threshold": 90},
        )

        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        saved = db.get(Prediction, prediction.id)

        assert saved is not None
        assert saved.metric == "cpu_usage"
        assert saved.predicted_value == 92.5
        assert saved.confidence_score == 0.95
        assert saved.details["threshold"] == 90

    finally:
        try:
            db.rollback()
            if service.id is not None:
                db.delete(service)
                db.commit()
        finally:
            db.close()


def test_remediation_action_can_be_persisted() -> None:
    db = SessionLocal()
    service = Service(
        name=f"test-remediation-{uuid4().hex}",
        namespace="default",
    )

    try:
        db.add(service)
        db.commit()
        db.refresh(service)

        incident = Incident(
            service_id=service.id,
            severity="high",
            probable_cause="High CPU utilization",
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        action = RemediationAction(
            incident_id=incident.id,
            action_type="scale",
            description="Scale deployment to three replicas",
            parameters={"replicas": 3},
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        saved = db.get(RemediationAction, action.id)

        assert saved is not None
        assert saved.status == "suggested"
        assert saved.action_type == "scale"
        assert saved.parameters["replicas"] == 3

    finally:
        try:
            db.rollback()

            if service.id is not None:
                incidents = db.scalars(
                    select(Incident).where(Incident.service_id == service.id)
                ).all()

                for incident in incidents:
                    db.delete(incident)

                db.commit()

                db.delete(service)
                db.commit()

        finally:
            db.close()


def test_audit_log_can_be_persisted() -> None:
    db = SessionLocal()
    audit_log = AuditLog(
        actor="system",
        action="incident.created",
        entity_type="incident",
        entity_id=123,
        details={
            "severity": "critical",
            "source": "anomaly_detector",
        },
    )

    try:
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        saved = db.get(AuditLog, audit_log.id)

        assert saved is not None
        assert saved.actor == "system"
        assert saved.action == "incident.created"
        assert saved.entity_type == "incident"
        assert saved.details["severity"] == "critical"

    finally:
        try:
            db.rollback()
            if audit_log.id is not None:
                db.delete(audit_log)
                db.commit()
        finally:
            db.close()
