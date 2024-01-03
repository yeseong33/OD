from django import forms

class InquiryResponseForm(forms.Form):
    response = forms.CharField(widget=forms.Textarea(attrs={'class': 'full-width-textarea'}))