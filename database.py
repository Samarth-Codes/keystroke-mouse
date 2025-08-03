import os
import json
import pickle
import base64
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./auth.db')

# For Supabase, the URL will look like: postgresql://postgres:[password]@[host]:[port]/postgres
if DATABASE_URL.startswith('postgresql://'):
    engine = create_engine(DATABASE_URL)
else:
    # Fallback to SQLite for local development
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Sample(Base):
    __tablename__ = "samples"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    features = Column(String)  # JSON-encoded features (keeping existing column name)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    model_data_base64 = Column(Text)  # Base64 encoded model
    model_type = Column(String)
    feature_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

class DatabaseManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        try:
            user = self.db.query(User).filter_by(username=username).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'created_at': user.created_at.isoformat()
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def create_user(self, username: str) -> Dict:
        """Create a new user."""
        try:
            user = User(username=username)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return {
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            print(f"Error creating user: {e}")
            raise
    
    def save_sample(self, user_id: int, features: List[float]) -> bool:
        """Save a keystroke sample."""
        try:
            features_json = json.dumps(features)
            sample = Sample(user_id=user_id, features=features_json)
            self.db.add(sample)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error saving sample: {e}")
            return False
    
    def get_user_samples(self, user_id: int) -> List[List[float]]:
        """Get all samples for a user."""
        try:
            samples = self.db.query(Sample).filter_by(user_id=user_id).all()
            result = []
            for sample in samples:
                try:
                    features = json.loads(sample.features)
                    result.append(features)
                except:
                    continue
            return result
        except Exception as e:
            print(f"Error getting samples: {e}")
            return []
    
    def save_model(self, username: str, model_data: bytes, model_type: str, feature_count: int) -> bool:
        """Save trained model as base64 string."""
        try:
            model_b64 = base64.b64encode(model_data).decode('utf-8')
            
            # Check if model already exists
            existing_model = self.db.query(Model).filter_by(username=username).first()
            if existing_model:
                # Update existing model
                existing_model.model_data_base64 = model_b64
                existing_model.model_type = model_type
                existing_model.feature_count = feature_count
            else:
                # Create new model
                model = Model(
                    username=username,
                    model_data_base64=model_b64,
                    model_type=model_type,
                    feature_count=feature_count
                )
                self.db.add(model)
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error saving model: {e}")
            return False
    
    def get_model(self, username: str) -> Optional[tuple]:
        """Get trained model for a user."""
        try:
            model = self.db.query(Model).filter_by(username=username).first()
            if model:
                model_data = base64.b64decode(model.model_data_base64)
                return (model_data, model.model_type, model.feature_count)
            return None
        except Exception as e:
            print(f"Error getting model: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users with sample counts."""
        try:
            users = self.db.query(User).all()
            result = []
            for user in users:
                sample_count = self.db.query(Sample).filter_by(user_id=user.id).count()
                result.append({
                    'username': user.username,
                    'enrollments': sample_count
                })
            return result
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        self.db.close() 