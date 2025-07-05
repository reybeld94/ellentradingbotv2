from app.database import SessionLocal
from app.services.auth_service import auth_service
import argparse


def main():
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", dest="full_name")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = auth_service.create_user(
            db=db,
            email=args.email,
            username=args.username,
            password=args.password,
            full_name=args.full_name,
        )
        user.is_admin = True
        db.commit()
        db.refresh(user)
        print(
            f"Admin user created: id={user.id} username={user.username} email={user.email}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
