from django import forms

class TeamCriteriaForm(forms.Form):
    country_checkbox = forms.BooleanField(required=False)
    age_checkbox = forms.BooleanField(required=False)
    experience_checkbox = forms.BooleanField(required=False)
    rank_checkbox = forms.BooleanField(required=False)
    
    country_priority = forms.FloatField(required=False, min_value=0, max_value=1, widget=forms.NumberInput(attrs={'step': '0.01', 'disabled': True}))
    age_priority = forms.FloatField(required=False, min_value=0, max_value=1, widget=forms.NumberInput(attrs={'step': '0.01', 'disabled': True}))
    experience_priority = forms.FloatField(required=False, min_value=0, max_value=1, widget=forms.NumberInput(attrs={'step': '0.01', 'disabled': True}))
    rank_priority = forms.FloatField(required=False, min_value=0, max_value=1, widget=forms.NumberInput(attrs={'step': '0.01', 'disabled': True}))
