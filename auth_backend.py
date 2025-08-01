from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
import os
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

app = FastAPI()

# Allow CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "keystroke-mouse-7h4m.vercel.app",  # Replace with your Vercel domain
        "http://localhost:5173",  # For local development
        "http://localhost:3000",  # Alternative local port
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database setup ---
DATABASE_URL = "sqlite:///./auth.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    samples = relationship("Sample", back_populates="user")

class Sample(Base):
    __tablename__ = "samples"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    features = Column(String)  # JSON-encoded list
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="samples")

Base.metadata.create_all(bind=engine)

DATA_DIR = "user_models"
os.makedirs(DATA_DIR, exist_ok=True)

class KeystrokeSample(BaseModel):
    username: str
    features: List[float]  # keystroke, mouse, typing rhythm, device/browser features

class AuthRequest(BaseModel):
    username: str
    features: List[float]  # keystroke, mouse, typing rhythm, device/browser features

@app.post("/enroll")
def enroll(sample: KeystrokeSample):
    db = SessionLocal()
    user = db.query(User).filter_by(username=sample.username).first()
    if not user:
        user = User(username=sample.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    db_sample = Sample(user_id=user.id, features=json.dumps(sample.features))
    db.add(db_sample)
    db.commit()
    model_path = os.path.join(DATA_DIR, f"{sample.username}.pkl")
    X, y = [], []
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            loaded = pickle.load(f)
            if len(loaded) == 4:
                model, X, y, prev_model_type = loaded
            else:
                model, X, y = loaded
                prev_model_type = "rf"
        expected_len = len(X[0])
        if len(sample.features) != expected_len:
            db.close()
            raise HTTPException(
                status_code=400,
                detail=f"Feature length mismatch: expected {expected_len}, got {len(sample.features)}"
            )
    # Add real sample
    X.append(sample.features)
    y.append(1)
    for _ in range(20):
        X.append(list(np.array(sample.features) + np.random.normal(0, 0.03, len(sample.features))))
        y.append(1)
    for _ in range(3):
        X.append(list(np.array(sample.features) + np.random.normal(0.2, 0.1, len(sample.features))))
        y.append(0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    models = {
        "rf": RandomForestClassifier(n_estimators=100),
        "svm": SVC(probability=True),
        "mlp": MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500)
    }
    best_model = None
    best_type = None
    best_score = -1
    for mtype, m in models.items():
        try:
            m.fit(X_train, y_train)
            preds = m.predict(X_test)
            score = f1_score(y_test, preds)
            if score > best_score:
                best_score = score
                best_model = m
                best_type = mtype
        except Exception as e:
            continue
    if best_model is None:
        db.close()
        raise HTTPException(status_code=500, detail="Model training failed for all models.")
    with open(model_path, "wb") as f:
        pickle.dump((best_model, X, y, best_type), f)
    db.close()
    return {"status": "enrolled", "model_type": best_type, "f1_score": best_score}

@app.post("/authenticate")
def authenticate(req: AuthRequest):
    model_path = os.path.join(DATA_DIR, f"{req.username}.pkl")
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="User not enrolled")
    with open(model_path, "rb") as f:
        model, X, y, model_type = pickle.load(f)
    expected_len = len(X[0])
    if len(req.features) != expected_len:
        raise HTTPException(
            status_code=400,
            detail=f"Feature length mismatch: expected {expected_len}, got {len(req.features)}"
        )
    proba = float(model.predict_proba([req.features])[0][1])
    is_genuine = bool(proba > 0.5)
    return {"authenticated": is_genuine, "confidence": proba, "model_type": model_type}

@app.get("/users")
def list_users():
    db = SessionLocal()
    users = db.query(User).all()
    result = []
    for user in users:
        count = db.query(Sample).filter_by(user_id=user.id).count()
        result.append({"username": user.username, "enrollments": count})
    db.close()
    return result

@app.get("/expected_feature_count")
def expected_feature_count(username: str = None):
    if username:
        model_path = os.path.join(DATA_DIR, f"{username}.pkl")
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                loaded = pickle.load(f)
                if len(loaded) == 4:
                    _, X, _, _ = loaded
                else:
                    _, X, _ = loaded
                return {"expected_feature_count": len(X[0])}
    # Default value if no user or model
    return {"expected_feature_count": 27}

# Mount static files at the end, after all API routes
app.mount("/", StaticFiles(directory=".", html=True), name="static") 
