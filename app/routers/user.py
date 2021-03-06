from fastapi import APIRouter, status, Response
from pony.orm import db_session, commit, RowNotFound, select
from datetime import datetime, date

from app.models import User
from app.models_api import NewUser, UpdateInfoUser
from app.tools import (
    is_valid_email,
    get_password_hash,
    verify_password,
    create_access_token,
    get_user_by_token,
    random_string,
)

router = APIRouter()


@router.post("/new")
@db_session
def new_user(u: NewUser, res: Response):
    email_valid, txt = is_valid_email(u.email)
    if email_valid is False:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return {"err": txt}
    txt = txt.strip().lower()
    curr_user = User.get(email=txt)
    if curr_user is None:
        hashed_pass = get_password_hash(u.password)
        today = date.today()
        create_date = datetime(today.year, today.month, today.day, 0, 0)
        User(
            email=txt,
            first_name=u.name,
            last_name=u.surname,
            password=hashed_pass,
            is_admin=False,
            create_date=create_date,
            hse_pass=random_string(16),
        )
        commit()
        return {"id": User.get(email=txt).id}
    else:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return {"err": f"User already exists with the same email and id {curr_user.id}"}


@router.get("/id/{id}")
@db_session
def get_user(id: int, token: str, res: Response):
    token_user, error, code = get_user_by_token(token)
    if error:
        res.status_code = code
        return error
    try:
        u = User[id]
    except RowNotFound:
        res.status_code = status.HTTP_404_NOT_FOUND
        return {"err": f"No user with id {id} found"}
    message = u.to_dict()
    message.pop("password", None)
    return message


@router.post("/authenticate")
@db_session
def user_auth(email: str, password: str, res: Response):
    email = email.strip().lower()
    curr_user = User.get(email=email)
    if curr_user is None:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return {"err": f"No user with email - {email} found"}
    is_valid_pass = verify_password(password, curr_user.password)
    if not is_valid_pass:
        res.status_code = status.HTTP_401_UNAUTHORIZED
        return {"err": f"Incorrect password"}
    access_token = create_access_token(data={"sub": curr_user.email})
    return {"access_token": access_token, "user_id": curr_user.id}


@router.post("/make_admin")
@db_session
def user_admin(id: int, token: str, is_admin: bool, res: Response):
    token_user, error, code = get_user_by_token(token)
    if error:
        res.status_code = code
        return error
    try:
        u = User[id]
    except RowNotFound:
        res.status_code = status.HTTP_404_NOT_FOUND
        return {"err": f"No user with id {id} found"}
    u.is_admin = is_admin
    commit()
    return {"id": u.id, "is_admin": u.is_admin}


@router.get("/all")
@db_session
def list_users(token: str, res: Response):
    token_user, error, code = get_user_by_token(token)
    if error:
        res.status_code = code
        return error

    if not token_user.is_admin:
        res.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {"err": f"User with email {token_user.email} is not admin!"}
    u = [x.to_dict() for x in select(u for u in User)[:]]

    return {"Users": u}


@router.post("/update_info")
@db_session
def update_user_info(user: UpdateInfoUser, token: str, res: Response):
    token_user, error, code = get_user_by_token(token)
    if error:
        res.status_code = code
        return error

    if token_user.id != user.id and not token_user.is_admin:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return {"err": "Non admin users can only update their info!"}

    try:
        user_for_update = User[user.id]
    except RowNotFound:
        user_for_update = None
    if user_for_update is None:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return {"err": f"No user with id {user.id} found!"}

    user_for_update.first_name = user.name
    user_for_update.last_name = user.surname
    commit()

    res = user_for_update.to_dict()
    res.pop("password", None)
    return res


@router.post("/update_password")
@db_session
def update_password(token: str, old_password: str, new_password: str, res: Response):
    token_user, error, code = get_user_by_token(token)
    if error:
        res.status_code = code
        return error
    is_valid_pass = verify_password(old_password, token_user.password)
    if not is_valid_pass:
        res.status_code = status.HTTP_401_UNAUTHORIZED
        return {"err": f"Incorrect old password"}

    hashed_new_pass = get_password_hash(new_password)
    token_user.password = hashed_new_pass

    return {"Success!"}
