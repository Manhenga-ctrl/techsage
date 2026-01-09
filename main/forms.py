from django import forms

class VoucherUploadForm(forms.Form):
    csv_file = forms.FileField()
