from sqlalchemy import select
from app.db import SessionLocal
from app.models.user import User
from app.auth.security import hash_password


def seed():
    db = SessionLocal()
    try:
        email = 'demo@smcc.local'
        user = db.scalar(select(User).where(User.email == email))
        if user:
            print('Demo user already exists:', email)
            return
        user = User(email=email, password_hash=hash_password('demo1234'))
        db.add(user)
        db.commit()
        print('Created demo user:', email, 'password=demo1234')
    finally:
        db.close()


if __name__ == '__main__':
    seed()
