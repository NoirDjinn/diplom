from pydantic import BaseModel


class NewUser(BaseModel):
    email: str
    name: str
    surname: str
    password: str


class UpdateInfoUser(BaseModel):
    id: int
    name: str
    surname: str


class CellType(BaseModel):
    id: int
    name: str


class PassType(BaseModel):
    id: int
    name: str


class UserGrowth(BaseModel):
    date: str = None
    count: int


class LeaseGrowth(BaseModel):
    date: str = None
    count: int


class EquipmentFreeRatio(BaseModel):
    id: int
    free: int
    total: int
    name: str = ""


class LeasesByType(BaseModel):
    type_id: int
    count: int
    name: str = ""


class LeasesByTypeAndDate(BaseModel):
    type_id: int
    count: int
    name: str = ""
    date: str = None
