from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

import models, schemas

# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()

def save_counted_workout(db: Session, sw: schemas.SaveWorkout):
    db_workout_flow = models.WorkoutFlow(workout_session=sw.workout_session, workout_name=sw.workout_name, sequence=sw.sequence,
                                set=sw.set, count=sw.count, breaktime = sw.breaktime)
    db.add(db_workout_flow)
    db.commit()
    db.refresh(db_workout_flow)

    return db_workout_flow

def save_workout_session(db: Session):

    db_workout_session = models.WorkoutSession()
    db.add(db_workout_session)
    db.commit()
    db.refresh(db_workout_session)

    return db_workout_session

def get_recent_session(db: Session):
    model = models.WorkoutSession
    return db.query(model).order_by(model.id.desc()).first()


def get_workout_flows_by_id(db: Session, id:int):
    return db.query(models.WorkoutFlow).filter(models.WorkoutFlow.id == id).all()

# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()

# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item