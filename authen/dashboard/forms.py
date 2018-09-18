from django import forms

class TestForm(forms.Form):
    name = forms.CharField(label='Name', max_length=20)
    checkbox = forms.BooleanField(label='check box')

class StockForm(forms.Form):
    SELECT_TYPE = (
        ('PB', 'PB Ratio'),
        ('PE', 'TTM Ratio')
    )
    stock_name = forms.CharField(label='Stock Code', max_length=6)
    days = forms.IntegerField(label='Days', min_value=100, max_value=3000)
    choice = forms.ChoiceField(label='PB/PE', choices=SELECT_TYPE)
