from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import database, models
from pydantic import BaseModel

router = APIRouter(
    prefix="/functions",
    tags=["functions"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FunctionCreate(BaseModel):
    name: str
    route: str
    language: str
    code: str
    timeout: int

class Function(FunctionCreate):
    id: int

    class Config:
        orm_mode = True

@router.post("/", response_model=Function, status_code=201)
async def create_function(function: FunctionCreate, db: Session = Depends(get_db)):
    db_function = db.query(models.Function).filter(models.Function.name == function.name).first()
    if db_function:
        raise HTTPException(status_code=400, detail="Function name already exists")

    db_function = models.Function(**function.dict())
    db.add(db_function)
    db.commit()
    db.refresh(db_function)
    return db_function

@router.get("/", response_model=list[Function])
async def read_functions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    functions = db.query(models.Function).offset(skip).limit(limit).all()
    return functions

@router.get("/{function_id}", response_model=Function)
async def read_function(function_id: int, db: Session = Depends(get_db)):
    db_function = db.query(models.Function).filter(models.Function.id == function_id).first()
    if not db_function:
        raise HTTPException(status_code=404, detail="Function not found")
    return db_function

@router.put("/{function_id}", response_model=Function)
async def update_function(function_id: int, function: FunctionCreate, db: Session = Depends(get_db)):
    db_function = db.query(models.Function).filter(models.Function.id == function_id).first()
    if not db_function:
        raise HTTPException(status_code=404, detail="Function not found")

    for key, value in function.dict().items():
        setattr(db_function, key, value)

    db.commit()
    db.refresh(db_function)
    return db_function

@router.delete("/{function_id}", response_model=dict)
async def delete_function(function_id: int, db: Session = Depends(get_db)):
    db_function = db.query(models.Function).filter(models.Function.id == function_id).first()
    if not db_function:
        raise HTTPException(status_code=404, detail="Function not found")

    db.delete(db_function)
    db.commit()
    return {"message": "Function deleted"}
