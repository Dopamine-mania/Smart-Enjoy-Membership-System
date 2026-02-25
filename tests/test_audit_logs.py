from app.db.session import SessionLocal
from app.repositories.admin_repository import AdminRepository
from app.models.admin import AdminUser
from app.core.security import hash_password


def test_audit_logs_include_admin_username():
    db = SessionLocal()
    try:
        admin = AdminUser(
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("not-default"),
            full_name="Admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        repo = AdminRepository(db)
        repo.create_audit_log(
            admin_user_id=admin.id,
            action="test",
            resource="audit_logs",
            details="hello",
        )
        db.commit()

        logs, total = repo.list_audit_logs(skip=0, limit=10)
        assert total == 1
        assert len(logs) == 1
        log, username = logs[0]
        assert log.admin_user_id == admin.id
        assert username == "admin"
    finally:
        db.close()

