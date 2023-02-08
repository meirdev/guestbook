import datetime

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


# Database

class Base(DeclarativeBase):
    pass


class GuestBookModel(Base):
    __tablename__ = "guestbook"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    message: Mapped[str]
    date: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


engine = create_engine("sqlite:///guestbook.db", echo=True, connect_args={"check_same_thread": False})

Base.metadata.create_all(engine)


# Models

class GuestBookScheme(BaseModel):
    name: str
    email: EmailStr
    message: str

    class Config:
        orm_mode = True


# API

app = FastAPI()

guestbook = APIRouter(prefix="/guestbook", tags=["guestbook"])


def get_session() -> Session:
    with Session(engine) as session:
        yield session


@guestbook.get("/", response_model=list[GuestBookScheme])
def read_all(session: Session = Depends(get_session)):
    stmt = select(GuestBookModel).order_by(GuestBookModel.date.desc())
    return session.scalars(stmt).all()


@guestbook.get("/{id}", response_model=GuestBookScheme)
def read_one(id: int, session: Session = Depends(get_session)):
    guestbook = session.get(GuestBookModel, id)
    return guestbook


@guestbook.post("/", response_model=GuestBookScheme)
def create(guestbook: GuestBookScheme, session: Session = Depends(get_session)):
    data = GuestBookModel(**guestbook.dict())
    session.add(data)
    session.commit()
    return data


@guestbook.put("/{id}", response_model=GuestBookScheme)
def update(id: int, guestbook: GuestBookScheme, session: Session = Depends(get_session)):
    guestbook_ = session.get(GuestBookModel, id)
    for key, value in guestbook.dict().items():
        setattr(guestbook_, key, value)
    session.commit()
    return guestbook_


@guestbook.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    guestbook = session.get(GuestBookModel, id)
    session.delete(guestbook)


app.include_router(guestbook)
