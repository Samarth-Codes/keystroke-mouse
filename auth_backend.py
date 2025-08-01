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
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from database import DatabaseManager

app = FastAPI()

# Allow CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://keystroke-mouse-7h4m.vercel.app",  # Your actual Vercel domain
        "http://localhost:5173",  # For local development
        "http://localhost:3000",  # Alternative local port
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class KeystrokeSample(BaseModel):
    username: str
    features: List[float]  # keystroke, mouse, typing rhythm, device/browser features

class AuthRequest(BaseModel):
    username: str
    features: List[float]  # keystroke, mouse, typing rhythm, device/browser features

@app.post("/enroll")
def enroll(sample: KeystrokeSample):
    db = DatabaseManager()
    try:
        # Get or create user
        user = db.get_user(sample.username)
        if not user:
            user = db.create_user(sample.username)
        
        # Save the sample
        if not db.save_sample(user['id'], sample.features):
            raise HTTPException(status_code=500, detail="Failed to save sample")
        
        # Get all samples for this user
        all_samples = db.get_user_samples(user['id'])
        
        # Check if we have enough samples to train a model
        if len(all_samples) < 1:
            raise HTTPException(status_code=400, detail="Not enough samples to train model")
        
        # Prepare training data
        X, y = [], []
        
        # Add real samples
        for sample_features in all_samples:
            if len(sample_features) == len(sample.features):  # Ensure consistent feature count
                X.append(sample_features)
                y.append(1)
        
        # Add synthetic positive samples (similar to real ones)
        for _ in range(min(20, len(X))):  # Add up to 20 synthetic positive samples
            if X:
                base_sample = X[0]  # Use first sample as base
                synthetic = list(np.array(base_sample) + np.random.normal(0, 0.03, len(base_sample)))
                X.append(synthetic)
                y.append(1)
        
        # Add synthetic negative samples
        for _ in range(3):
            if X:
                base_sample = X[0]
                synthetic = list(np.array(base_sample) + np.random.normal(0.2, 0.1, len(base_sample)))
                X.append(synthetic)
                y.append(0)
        
        if len(X) < 2:
            raise HTTPException(status_code=400, detail="Not enough data to train model")
        
        # Train model
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
                print(f"Model {mtype} failed: {e}")
                continue
        
        if best_model is None:
            raise HTTPException(status_code=500, detail="Model training failed for all models.")
        
        # Save the model
        model_bytes = pickle.dumps(best_model)
        if not db.save_model(sample.username, model_bytes, best_type, len(sample.features)):
            raise HTTPException(status_code=500, detail="Failed to save model")
        
        return {
            "status": "enrolled", 
            "model_type": best_type, 
            "f1_score": best_score,
            "samples_count": len(all_samples)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")
    finally:
        db.close()

@app.post("/authenticate")
def authenticate(req: AuthRequest):
    db = DatabaseManager()
    try:
        # Get user
        user = db.get_user(req.username)
        if not user:
            raise HTTPException(status_code=404, detail="User not enrolled")
        
        # Get model
        model_data = db.get_model(req.username)
        if not model_data:
            raise HTTPException(status_code=404, detail="User model not found")
        
        model_bytes, model_type, expected_len = model_data
        model = pickle.loads(model_bytes)
        
        if len(req.features) != expected_len:
            raise HTTPException(
                status_code=400,
                detail=f"Feature length mismatch: expected {expected_len}, got {len(req.features)}"
            )
        
        # Predict
        try:
            proba = float(model.predict_proba([req.features])[0][1])
            is_genuine = bool(proba > 0.5)
            return {
                "authenticated": is_genuine, 
                "confidence": proba, 
                "model_type": model_type
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail="Model prediction failed")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
    finally:
        db.close()

@app.get("/users")
def list_users():
    db = DatabaseManager()
    try:
        return db.get_all_users()
    except Exception as e:
        print(f"Error listing users: {e}")
        return []
    finally:
        db.close()

@app.get("/expected_feature_count")
def expected_feature_count(username: str = None):
    if not username:
        return {"expected_feature_count": 27}
    
    db = DatabaseManager()
    try:
        model_data = db.get_model(username)
        if model_data:
            _, _, feature_count = model_data
            return {"expected_feature_count": feature_count}
        
        # Default value if no user or model
        return {"expected_feature_count": 27}
    except Exception as e:
        print(f"Error getting feature count: {e}")
        return {"expected_feature_count": 27}
    finally:
        db.close()

# Mount static files at the end, after all API routes
app.mount("/", StaticFiles(directory=".", html=True), name="static") 
