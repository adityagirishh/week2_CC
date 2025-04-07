from fastapi import FastAPI
from .routes import functions
from .models import database
   
app = FastAPI()
   
app.include_router(functions.router)
   
@app.on_event("startup")
async def startup():
    database.Base.metadata.create_all(bind=database.engine)
   
@app.on_event("shutdown")
async def shutdown():
    database.database.dispose()
   
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)