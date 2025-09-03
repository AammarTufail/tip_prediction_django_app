from django import forms

class TipPredictionForm(forms.Form):
    SEX_CHOICES = [
        ('Female', 'Female'),
        ('Male', 'Male'),
    ]
    
    SMOKER_CHOICES = [
        ('No', 'No'),
        ('Yes', 'Yes'),
    ]
    
    DAY_CHOICES = [
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
        ('Thur', 'Thursday'),
    ]
    
    TIME_CHOICES = [
        ('Dinner', 'Dinner'),
        ('Lunch', 'Lunch'),
    ]
    
    total_bill = forms.FloatField(
        label='Total Bill ($)',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter total bill amount',
            'step': '0.01'
        })
    )
    
    sex = forms.ChoiceField(
        label='Gender',
        choices=SEX_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    smoker = forms.ChoiceField(
        label='Smoker',
        choices=SMOKER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    day = forms.ChoiceField(
        label='Day of Week',
        choices=DAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    time = forms.ChoiceField(
        label='Time',
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    size = forms.IntegerField(
        label='Party Size',
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of people'
        })
    )
