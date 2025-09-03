# Python ML model deployment with Django

This repository demonstrates how to deploy a machine learning model using Django, a high-level Python web framework. The project includes a simple web interface that allows users to input data and receive predictions from the ML model.

> Create a readme.md file of your project.

## 1. Create python env

We will use python env to create the env.

```bash
# create a virtual environment
python -m venv .venv
# activate the virtual environment for linux mac 
source .venv/bin/activate
# for windows
# .venv\Scripts\activate
# for windows and git bash
source .venv/Scripts/activate
```

## 2. Install python libraries

```bash
# web development framework
pip install django
# machine learning libraries
pip install numpy pandas matplotlib seaborn plotly scikit-learn xgboost
# jupyter notebook support
pip install ipykernel
```

## 3. Train your machine learning model

1. Find the data
2. Preprocess the data
3. Train the model
4. Evaluate the model
5. Save the model

I have saved the model as `xgb_model.pkl` in the `models` directory.
> You can see the procedure of ML training a model and saving it in this [Jupyter notebook](./ml_project/01_ml.ipynb).

## 4. Create a Django project

```bash
django-admin startproject tip_prediction
cd tip_prediction
```

## 5. Create a Django app

```bash
python manage.py startapp ml_app
```

## 6. Update settings.py

Add the new app to the `INSTALLED_APPS` list in `tip_prediction/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'ml_app',
]
```

## 7. Create a form for user input

In `ml_app/forms.py`, create a form to accept user input:

```python
from django import forms

class PredictionForm(forms.Form):
    feature1 = forms.FloatField(label='Feature 1')
    feature2 = forms.FloatField(label='Feature 2')
    feature3 = forms.FloatField(label='Feature 3')
    feature4 = forms.FloatField(label='Feature 4')
    feature5 = forms.FloatField(label='Feature 5')
    feature6 = forms.FloatField(label='Feature 6')
```

