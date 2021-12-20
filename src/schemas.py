from pydantic import BaseModel


class Offer(BaseModel):
    sdp: str
    type: str
    exercise: str
    cnt: str
    set: str
    breaktime: str

class Info(BaseModel):
    exercise: str
    cnt: str
    set: str
    breaktime: str
class Live(BaseModel):
    sdp: str
    type: str
