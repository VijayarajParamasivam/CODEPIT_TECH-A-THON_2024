from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
import pandas as pd
from .services.data_fetcher import fetch_stock_data,fetch_current_stock_data
from .services.predictor import predict_stock_price
from fastapi.responses import JSONResponse, StreamingResponse
import io
import xml.etree.ElementTree as ET
import numpy as np
import app.database as database
from app.utils import hash_password,verify_password, create_access_token,SECRET_KEY,ALGORITHM
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select




app = FastAPI()
database.init_db()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(database.get_db)):
    hashed_password = hash_password(user.password)
    try:
        database.create_user(db, username=user.username, email=user.email, hashed_password=hashed_password)
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "subscription": user.subscription_level})
    return {"access_token": access_token, "token_type": "bearer"}


@app.patch("/user/subscription")
async def switch_subscription(
    new_subscription: str = Query(..., description="New subscription level"),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        query = select(database.User).filter(database.User.username == username)
        result = await db.execute(query)
        user = result.scalars().first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if new_subscription not in ['basic', 'premium']:
        raise HTTPException(status_code=400, detail="Invalid subscription type")
    
    user.subscription_level = new_subscription
    db.add(user)
    await db.commit()
    return {"message": f"Subscription level changed to {new_subscription}"}

@app.delete("/user/delete")
async def delete_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.query(database.User).filter(database.User.username == username).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db.delete(user)
    db.commit()
    return {"message": "User account deleted"}


def convert_to_xml(data: pd.DataFrame) -> str:
    """Convert DataFrame to XML string"""
    root = ET.Element("Data")
    for index, row in data.iterrows():
        record = ET.SubElement(root, "Record", {"Date": str(index)})
        for col, val in row.items():
            ET.SubElement(record, col).text = str(val) if pd.notna(val) else "None"
    return ET.tostring(root, encoding='unicode')

def convert_to_dict(data: pd.DataFrame) -> dict:
    """Convert DataFrame to a JSON serializable dictionary"""
    # Convert Timestamp to string and handle NaN values
    data = data.replace({np.nan: None})
    data.index = data.index.strftime('%Y-%m-%d')  # Convert index to string format
    return data.to_dict(orient="index")

@app.get("/stocks/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    frequency: Optional[str] = Query('daily'),
    format: Optional[str] = Query('json'),
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)):

    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.query(database.User).filter(database.User.username == username).first()
        if user is None:
            raise credentials_exception
        
        try:
        # Fetch stock data
            data = fetch_stock_data(symbol, start_date, end_date, frequency)
        
        # Convert data to a JSON serializable format
            if format == 'json':
                return JSONResponse(content=convert_to_dict(data))
            elif format == 'csv':
                csv_data = data.to_csv()
                return StreamingResponse(io.StringIO(csv_data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=historical_data.csv"})
            elif format == 'xml':
                xml_data = convert_to_xml(data)
                return StreamingResponse(io.StringIO(xml_data), media_type="application/xml", headers={"Content-Disposition": "attachment; filename=historical_data.xml"})
            else:
                raise HTTPException(status_code=400, detail="Invalid format. Supported formats: json, csv, xml.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    except JWTError:
        raise credentials_exception
    
    
    
@app.get("/stocks/{symbol}/current")
async def get_current_price(symbol: str,token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)):

    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.query(database.User).filter(database.User.username == username).first()
        if user is None:
            raise credentials_exception
        
        try:
            current_data = fetch_current_stock_data(symbol)
            return current_data.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    except JWTError:
        raise credentials_exception
    

@app.get("/stocks/{symbol}/predict")
def predict_stock(symbol: str, periods: int = 5):
    try:
        forecast = predict_stock_price(symbol, periods)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
