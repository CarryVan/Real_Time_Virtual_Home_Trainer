from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

import models, schemas

def save_counted_workout(db: Session, sw: schemas.SaveWorkout):
    db_workout_flow = models.WorkoutFlow(workout_session=sw.workout_session, workout_name=sw.workout_name, sequence=sw.sequence,
                                set=sw.set, count=sw.count, breaktime = sw.breaktime)
    db.add(db_workout_flow)
    db.commit()
    db.refresh(db_workout_flow)

    return db_workout_flow

def save_workout_session(db: Session, exit: int):

    db_workout_session = models.WorkoutSession(exit = exit)
    db.add(db_workout_session)
    db.commit()
    db.refresh(db_workout_session)

    return db_workout_session

def get_recent_session(db: Session):
    model = models.WorkoutSession
    return db.query(model).order_by(model.id.desc()).first()

def get_recent_sessions(db: Session):
    model = models.WorkoutSession
    return db.query(model).order_by(model.id.desc()).limit(10).all()

def get_workout_flows_by_id(db: Session, id:int):
    return db.query(models.WorkoutFlow).filter(models.WorkoutFlow.workout_session == id).all()
