from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from tensorflow.keras.models import load_model
from io import BytesIO
from PIL import Image
import os
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Get the absolute path to the models directory
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
print(f"Looking for models in: {MODELS_DIR}")

try:
    # Load models with absolute paths
    model1_path = os.path.join(MODELS_DIR, "brain_stroke.keras")
    model2_path = os.path.join(MODELS_DIR, "lung_cancer.keras")
    
    # Verify files exist
    if not os.path.exists(model1_path):
        raise FileNotFoundError(f"Brain stroke model not found at: {model1_path}")
    if not os.path.exists(model2_path):
        raise FileNotFoundError(f"Lung cancer model not found at: {model2_path}")
        
    print(f"Loading models from:\n{model1_path}\n{model2_path}")
    
    model1 = load_model(model1_path)
    model2 = load_model(model2_path)
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {str(e)}")
    raise

@app.get("/")
async def root():
    return {"message": "FastAPI server is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": True,
        "model_paths": {
            "stroke": model1_path,
            "cancer": model2_path
        }
    }

@app.post("/predict")
async def predict(image: UploadFile = File(...), analysis_type: str = "stroke"):
    try:
        # Validate file type
        if not (image.filename.endswith('.jpg') or image.filename.endswith('.png')):
            raise HTTPException(
                status_code=400,
                detail="Only .jpg and .png images are accepted."
            )

        # Process image
        contents = await image.read()
        img = Image.open(BytesIO(contents))
        img = img.resize((224, 224))
        img = img.convert("RGB")
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Choose model based on analysis type
        if analysis_type.lower() == "stroke":
            prediction = float(model1.predict(img_array)[0])
            if prediction >= 0.5:
                result = {
                    "prediction": "stroke",
                    "probability": float(prediction),
                    "message": "There might be a possibility of a stroke. Please consult a doctor immediately."
                }
            else:
                result = {
                    "prediction": "normal",
                    "probability": float(1 - prediction),
                    "message": "No concerning indicators detected. However, always consult healthcare professionals for medical advice."
                }
        else:  # lung cancer
            prediction = float(model2.predict(img_array)[0])
            if prediction >= 0.5:
                result = {
                    "prediction": "cancer",
                    "probability": float(prediction),
                    "message": "Potential indicators of lung cancer detected. Please consult a specialist immediately."
                }
            else:
                result = {
                    "prediction": "normal",
                    "probability": float(1 - prediction),
                    "message": "No concerning indicators detected. However, always consult healthcare professionals for medical advice."
                }

        return result

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing the image: {str(e)}")

if __name__ == "__main__":
    print("Starting FastAPI server...")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print(f"Error starting server: {str(e)}")