# website/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Record, TenantImage, Property, CustomUser, Folder, Document, Task, TaskImage, TenantPropertyRelationship
from dal import autocomplete

# Custom widget for DateField to show a native HTML5 date picker
class DateInput(forms.DateInput):
    input_type = 'date'

# Custom widget for multiple file input
class MultipleFileInput(forms.FileInput):
    # CRITICAL CHANGE: Explicitly tell Django this widget allows multiple selections
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        # Ensure 'multiple' HTML attribute is set for the browser
        if attrs is None:
            attrs = {}
        attrs['multiple'] = 'multiple' # Set the HTML attribute
        super().__init__(attrs)

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = '__all__'
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postcode'
            }),
            'next_of_kin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Next of Kin'
            }),
            'current_residence': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current Residence'
            }),
            'occupancy_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'move_in_date': DateInput(attrs={
                'class': 'form-control'
            }),
            'move_out_date': DateInput(attrs={
                'class': 'form-control'
            }),
            'key_collection': DateInput(attrs={
                'class': 'form-control'
            }),
            'key_drop_off': DateInput(attrs={
                'class': 'form-control'
            }),
        }

class TenantImageForm(forms.ModelForm):
    class Meta:
        model = TenantImage
        fields = ['image', 'category', 'description'] 
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.TextInput(attrs={ 
                'class': 'form-control',
                'placeholder': 'Optional: e.g., "Front door photo", "Passport scan"'
            }),
        }

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name', 'address', 'postcode', 'property_type',
            'gas_certificate_expiry_date',
            'electric_certificate_expiry_date',
            'epc_certificate_expiry_date',
            'fra_certificate_expiry_date',
            'building_insurance_expiry_date',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 12 Baker Street'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full address'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. W1U 3AA'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'gas_certificate_expiry_date': DateInput(attrs={'class': 'form-control'}),
            'electric_certificate_expiry_date': DateInput(attrs={'class': 'form-control'}),
            'epc_certificate_expiry_date': DateInput(attrs={'class': 'form-control'}),
            'fra_certificate_expiry_date': DateInput(attrs={'class': 'form-control'}),
            'building_insurance_expiry_date': DateInput(attrs={'class': 'form-control'}),
        }


# Custom User Forms for the CustomUser model
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class DocumentForm(forms.ModelForm):
    # Use the custom MultipleFileInput widget
    file = forms.FileField(widget=MultipleFileInput(attrs={'class': 'form-control'}))
    description = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Optional: Add a description for all files'
        }),
        label='Description'
    )

    class Meta:
        model = Document
        fields = ['file', 'description'] 

    def __init__(self, *args, **kwargs):
        self.property_instance = kwargs.pop('property_instance', None) 
        super().__init__(*args, **kwargs)


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
        
    def __init__(self, *args, **kwargs):
        self.property_instance = kwargs.pop('property_instance', None)
        self.parent_folder = kwargs.pop('parent_folder', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'}) # Apply Bootstrap class

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Folder.objects.filter(property=self.property_instance, parent=self.parent_folder, name=name).exists():
            raise forms.ValidationError("A folder with this name already exists in this location.")
        return name

# --- New Forms for Tasks ---

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'job_id', 'property', 'tenant', 'date_issue_reported',
            'description_of_issue', 'job_allocated', 'date_completed'
        ]
        widgets = {
            'date_issue_reported': DateInput(attrs={'class': 'form-control'}),
            'date_completed': DateInput(attrs={'class': 'form-control'}),
            'description_of_issue': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'job_id': forms.TextInput(attrs={'class': 'form-control'}),
            'property': autocomplete.ModelSelect2(url='property-autocomplete', attrs={'class': 'form-select'}), # Ensure Bootstrap class
            'tenant': autocomplete.ModelSelect2(url='tenant-autocomplete', attrs={'class': 'form-select'}), # Ensure Bootstrap class
            'job_allocated': forms.Select(attrs={'class': 'form-select'}),
        }

class TaskImageForm(forms.ModelForm):
    class Meta:
        model = TaskImage
        fields = ['image', 'image_type']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image_type': forms.Select(attrs={'class': 'form-select'}),
        }

# --- New form for TenantPropertyRelationship ---
class TenantPropertyRelationshipForm(forms.ModelForm):
    class Meta:
        model = TenantPropertyRelationship
        # 'property' field is set in the view as it's a hidden field tied to the URL's PK
        fields = ['tenant', 'move_in_date', 'move_out_date']
        widgets = {
            'tenant': autocomplete.ModelSelect2(url='tenant-autocomplete', attrs={'class': 'form-select'}),
            'move_in_date': DateInput(attrs={'class': 'form-control'}), # Use DateInput for consistency
            'move_out_date': DateInput(attrs={'class': 'form-control'}), # Use DateInput for consistency
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The 'tenant' field uses dal_select2, which will render a select element.
        # Ensure it has the Bootstrap form-select class applied.
        # This is often handled by the autocomplete widget directly, but explicit setting can help.
        self.fields['tenant'].widget.attrs['class'] = 'form-select'
