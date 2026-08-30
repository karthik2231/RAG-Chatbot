"""Utility script to promote a user to admin role."""

import sys

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, UserRole


def promote_to_admin(email: str) -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}")
            sys.exit(1)
        user.role = UserRole.ADMIN
        db.commit()
        print(f"Promoted {email} to admin")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_admin.py user@example.com")
        sys.exit(1)
    promote_to_admin(sys.argv[1])
