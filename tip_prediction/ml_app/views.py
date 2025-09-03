from django.shortcuts import render
from django.contrib import messages
from .forms import TipPredictionForm
import joblib
import numpy as np
import os
from django.conf import settings

# Load the trained model
model_path = os.path.join(settings.BASE_DIR.parent, 'ml_project', 'models', 'xgb_model.pkl')

def load_model():
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def encode_features(sex, smoker, day, time):
    """
    Encode categorical features according to the training process
    Based on the notebook, the encoding was:
    sex: Female=0, Male=1
    smoker: No=0, Yes=1  
    day: Fri=0, Sat=1, Sun=2, Thur=3
    time: Dinner=0, Lunch=1
    """
    
    # Encode sex
    sex_encoded = 1 if sex == 'Male' else 0
    
    # Encode smoker
    smoker_encoded = 1 if smoker == 'Yes' else 0
    
    # Encode day
    day_mapping = {'Fri': 0, 'Sat': 1, 'Sun': 2, 'Thur': 3}
    day_encoded = day_mapping.get(day, 0)
    
    # Encode time
    time_encoded = 1 if time == 'Lunch' else 0
    
    return sex_encoded, smoker_encoded, day_encoded, time_encoded

def index(request):
    """Main landing page"""
    return render(request, 'ml_app/index.html')

def predict_tip(request):
    """Tip prediction page"""
    prediction = None
    
    if request.method == 'POST':
        form = TipPredictionForm(request.POST)
        if form.is_valid():
            # Get form data
            total_bill = form.cleaned_data['total_bill']
            sex = form.cleaned_data['sex']
            smoker = form.cleaned_data['smoker']
            day = form.cleaned_data['day']
            time = form.cleaned_data['time']
            size = form.cleaned_data['size']
            
            # Encode categorical features
            sex_encoded, smoker_encoded, day_encoded, time_encoded = encode_features(
                sex, smoker, day, time
            )
            
            # Prepare features for prediction
            features = np.array([[total_bill, sex_encoded, smoker_encoded, day_encoded, time_encoded, size]])
            
            # Load model and make prediction
            model = load_model()
            if model:
                try:
                    prediction = model.predict(features)[0]
                    prediction = round(prediction, 2)
                    messages.success(request, f'Prediction successful! Expected tip: ${prediction}')
                except Exception as e:
                    messages.error(request, f'Error making prediction: {str(e)}')
            else:
                messages.error(request, 'Error: Could not load the ML model.')
    else:
        form = TipPredictionForm()
    
    context = {
        'form': form,
        'prediction': prediction,
    }
    
    return render(request, 'ml_app/predict_tip.html', context)
