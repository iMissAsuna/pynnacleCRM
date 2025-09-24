import datetime
import os
from collections import defaultdict
from dal import autocomplete
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import F, Min, Q
from calendar import monthrange
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.text import slugify

# Import the new model and form
from .models import Record, TenantImage, Property, Folder, Document, Task, TaskImage, TenantPropertyRelationship
from .forms import RecordForm, TenantImageForm, PropertyForm, CustomUserCreationForm, CustomUserChangeForm, DocumentForm, FolderForm, TaskForm, TaskImageForm, TenantPropertyRelationshipForm

# --- Helper Form for Deleting TenantPropertyRelationship (not a ModelForm) ---
class TenantPropertyRelationshipDeleteForm(forms.Form):
    relationship_id = forms.IntegerField(widget=forms.HiddenInput())

# ---------------------------
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error logging in, please try again.")
            return redirect('home')

    return render(request, 'home.html')

def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out!")
    return redirect('home')

# ---------------------------
# Dashboard & Sidebar Views
# ---------------------------

@login_required
def dashboard(request):
    today = datetime.date.today()
    seven_days_from_now = today + datetime.timedelta(days=7)

    expired_certs = []
    due_today_certs = []
    expiring_soon_certs = []
    monthly_certs_filtered = []

    properties = Property.objects.all()

    CERT_FIELD_MAP = {
        'Gas Certificate': 'gas_certificate_expiry_date',
        'Electric Certificate': 'electric_certificate_expiry_date',
        'EPC Certificate': 'epc_certificate_expiry_date',
        'FRA Certificate': 'fra_certificate_expiry_date',
        'Building Insurance': 'building_insurance_expiry_date',
    }

    for prop in properties:
        for cert_type_name, field_name in CERT_FIELD_MAP.items():
            expiry_date = getattr(prop, field_name)
            if expiry_date:
                cert_info = {
                    'property_name': prop.name,
                    'property_pk': prop.pk,
                    'cert_type': cert_type_name,
                    'expiry_date': expiry_date
                }
                if expiry_date < today:
                    expired_certs.append(cert_info)
                elif expiry_date == today:
                    due_today_certs.append(cert_info)
                elif expiry_date > today and expiry_date <= seven_days_from_now:
                    expiring_soon_certs.append(cert_info)

    expired_certs.sort(key=lambda x: x['expiry_date'])
    due_today_certs.sort(key=lambda x: x['expiry_date'])
    expiring_soon_certs.sort(key=lambda x: x['expiry_date'])

    selected_month = None
    selected_year = None
    selected_month_name = None

    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    current_year = today.year
    years = list(range(current_year - 5, current_year + 10))

    try:
        month_param = request.GET.get('month')
        year_param = request.GET.get('year')

        if month_param and year_param:
            selected_month = int(month_param)
            selected_year = int(year_param)

            if not (1 <= selected_month <= 12) or not (1900 <= selected_year <= 2100):
                raise ValueError("Invalid month or year")

            selected_month_name = datetime.date(selected_year, selected_month, 1).strftime('%B')

            num_days = monthrange(selected_year, selected_month)[1]
            start_date = datetime.date(selected_year, selected_month, 1)
            end_date = datetime.date(selected_year, selected_month, num_days)

            for prop in properties:
                for cert_type_name, field_name in CERT_FIELD_MAP.items():
                    expiry_date = getattr(prop, field_name)
                    if expiry_date and start_date <= expiry_date <= end_date:
                        monthly_certs_filtered.append({
                            'property_name': prop.name,
                            'property_pk': prop.pk,
                            'cert_type': cert_type_name,
                            'expiry_date': expiry_date
                        })
            monthly_certs_filtered.sort(key=lambda x: x['expiry_date'])

    except (ValueError, TypeError):
        messages.error(request, "Invalid month or year selected for filtering.")
        selected_month = None
        selected_year = None
        selected_month_name = None

    if selected_month is None:
        selected_month = today.month
    if selected_year is None:
        selected_year = today.year

    if selected_month_name is None and selected_month is not None:
        selected_month_name = datetime.date(selected_year, selected_month, 1).strftime('%B')

    return render(request, 'dashboard.html', {
        'expired_certs': expired_certs,
        'due_today_certs': due_today_certs,
        'expiring_soon_certs': expiring_soon_certs,
        'monthly_certs_filtered': monthly_certs_filtered,
        'today': today,
        'months': months,
        'years': years,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_name': selected_month_name,
    })

@login_required
def logbook(request):
    sort_by = request.GET.get('sort_by', 'job_id_asc')
    tasks = Task.objects.all()

    if sort_by == 'pending':
        tasks = tasks.order_by(F('date_completed').asc(nulls_first=True), '-date_issue_reported')
    elif sort_by == 'not_pending':
        tasks = tasks.order_by(F('date_completed').desc(nulls_last=True), '-date_completed')
    elif sort_by == 'completed_asc':
        tasks = tasks.order_by(F('date_completed').asc(nulls_last=True))
    elif sort_by == 'completed_desc':
        tasks = tasks.order_by(F('date_completed').desc(nulls_first=True))
    elif sort_by == 'reported_asc':
        tasks = tasks.order_by('date_issue_reported')
    elif sort_by == 'reported_desc':
        tasks = tasks.order_by('-date_issue_reported')
    elif sort_by == 'job_id_desc':
        tasks = tasks.order_by('-job_id')
    else:
        tasks = tasks.order_by('job_id')

    context = {
        'tasks': tasks,
        'current_sort': sort_by,
    }
    return render(request, 'logbook.html', context)

@login_required
def maintenance(request):
    return render(request, 'maintenance.html')

@login_required
def certificates(request):
    return render(request, 'certificates.html')

@login_required
def archive(request):
    return render(request, 'archive.html')

@login_required
def keys_register(request):
    return render(request, 'keys_register.html')

@login_required
def cleaning(request):
    return render(request, 'cleaning.html')

# ---------------------------
# Tenant Views
# ---------------------------

@login_required
def tenants_list(request):
    query = request.GET.get('q')
    
    if query:
        records = Record.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        ).order_by('last_name', 'first_name')
    else:
        records = Record.objects.all().order_by('last_name', 'first_name')

    context = {
        'records': records,
        'query': query,
    }
    return render(request, 'tenants_list.html', context)

@login_required
def add_record(request):
    if request.method == 'POST':
        form = RecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tenant added successfully!")
            return redirect('tenants_list')
        else:
            messages.error(request, "Error adding tenant. Please check the form.")
    else:
        form = RecordForm()
    
    context = {
        'form': form,
    }
    return render(request, 'add_record.html', context)

@login_required
def tenant_record(request, pk):
    record = get_object_or_404(Record, pk=pk)
    form = RecordForm(instance=record)
    edit_mode = False

    if request.method == 'POST':
        if 'edit_mode' in request.POST:
            edit_mode = True
        elif 'cancel_edit' in request.POST:
            edit_mode = False
        elif 'save_details' in request.POST:
            form = RecordForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
                messages.success(request, "Tenant details updated successfully!")
                return redirect('record', pk=pk)
            edit_mode = True

    context = {
        'record': record,
        'form': form,
        'edit_mode': edit_mode,
    }
    return render(request, 'website/tenant.html', context)

@login_required
def delete_image(request, image_id):
    image_item = get_object_or_404(TenantImage, pk=image_id)
    record_pk = image_item.record.pk
    image_item.delete()
    messages.success(request, "Tenant image deleted successfully.")
    return redirect('record', pk=record_pk)

# ---------------------------
# Property Views
# ---------------------------

@login_required
def properties_list(request):
    sort_by = request.GET.get('sort', 'name_asc')
    query = request.GET.get('q')
    properties_queryset = Property.objects.all()

    if query:
        properties_queryset = properties_queryset.filter(
            Q(name__icontains=query) | Q(address__icontains=query)
        ).distinct()

    if sort_by == 'name_asc':
        properties = properties_queryset.order_by('name')
    elif sort_by == 'name_desc':
        properties = properties_queryset.order_by('-name')
    elif sort_by == 'type':
        properties = properties_queryset.order_by('property_type')
    elif sort_by == 'recent':
        properties = properties_queryset.order_by('-updated_at')
    elif sort_by == 'oldest':
        properties = properties_queryset.order_by('updated_at')
    elif sort_by == 'overall_soonest':
        properties_list = list(properties_queryset)
        def get_soonest_overall_expiry(prop):
            expiry_dates = []
            if prop.gas_certificate_expiry_date: expiry_dates.append(prop.gas_certificate_expiry_date)
            if prop.electric_certificate_expiry_date: expiry_dates.append(prop.electric_certificate_expiry_date)
            if prop.epc_certificate_expiry_date: expiry_dates.append(prop.epc_certificate_expiry_date)
            if prop.fra_certificate_expiry_date: expiry_dates.append(prop.fra_certificate_expiry_date)
            if prop.building_insurance_expiry_date: expiry_dates.append(prop.building_insurance_expiry_date)
            if expiry_dates:
                return min(expiry_dates)
            return datetime.date.max
        properties_list.sort(key=get_soonest_overall_expiry)
        properties = properties_list
    elif sort_by == 'overall_furthest':
        properties_list = list(properties_queryset)
        def get_furthest_overall_expiry(prop):
            expiry_dates = []
            if prop.gas_certificate_expiry_date: expiry_dates.append(prop.gas_certificate_expiry_date)
            if prop.electric_certificate_expiry_date: expiry_dates.append(prop.electric_certificate_expiry_date)
            if prop.epc_certificate_expiry_date: expiry_dates.append(prop.epc_certificate_expiry_date)
            if prop.fra_certificate_expiry_date: expiry_dates.append(prop.fra_certificate_expiry_date)
            if prop.building_insurance_expiry_date: expiry_dates.append(prop.building_insurance_expiry_date)
            if expiry_dates:
                return max(expiry_dates)
            return datetime.date.min
        properties_list.sort(key=get_furthest_overall_expiry, reverse=True)
        properties = properties_list
    elif sort_by == 'gas_soonest':
        properties = properties_queryset.order_by(F('gas_certificate_expiry_date').asc(nulls_last=True))
    elif sort_by == 'electric_soonest':
        properties = properties_queryset.order_by(F('electric_certificate_expiry_date').asc(nulls_last=True))
    elif sort_by == 'epc_soonest':
        properties = properties_queryset.order_by(F('epc_certificate_expiry_date').asc(nulls_last=True))
    elif sort_by == 'fra_soonest':
        properties = properties_queryset.order_by(F('fra_certificate_expiry_date').asc(nulls_last=True))
    elif sort_by == 'building_insurance_soonest':
        properties = properties_queryset.order_by(F('building_insurance_expiry_date').asc(nulls_last=True))
    elif sort_by == 'gas_furthest':
        properties = properties_queryset.order_by(F('gas_certificate_expiry_date').desc(nulls_first=True))
    elif sort_by == 'electric_furthest':
        properties = properties_queryset.order_by(F('electric_certificate_expiry_date').desc(nulls_first=True))
    elif sort_by == 'epc_furthest':
        properties = properties_queryset.order_by(F('epc_certificate_expiry_date').desc(nulls_first=True))
    elif sort_by == 'fra_furthest':
        properties = properties_queryset.order_by(F('fra_certificate_expiry_date').desc(nulls_first=True))
    elif sort_by == 'building_insurance_furthest':
        properties = properties_queryset.order_by(F('building_insurance_expiry_date').desc(nulls_first=True))
    else:
        properties = properties_queryset.order_by('name')

    return render(request, 'properties.html', {
        'properties': properties,
        'sort_by': sort_by,
        'query': query,
    })

@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Property added successfully!")
            return redirect('properties_list')
        else:
            messages.error(request, "Error adding property. Please check the form.")
    else:
        form = PropertyForm()

    return render(request, 'property_form.html', {
        'form': form,
        'title': 'Add Property'
    })

@login_required
def edit_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            form.save()
            messages.success(request, "Property details updated successfully!")
            return redirect('properties_list')
        else:
            messages.error(request, "Error updating property. Please check the form.")
    else:
        form = PropertyForm(instance=property)

    return render(request, 'property_form.html', {
        'form': form,
        'title': 'Edit Property'
    })

@login_required
def delete_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    try:
        property.delete()
        messages.success(request, "Property deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting property: {str(e)}")
    return redirect('properties_list')

@login_required
def property_detail(request, pk, active_tab='building-insurance'):
    property_obj = get_object_or_404(Property, pk=pk)
    document_tabs_slug_to_name_map = {
        'building-insurance': 'Building Insurance',
        'electrical-certificate': 'Electric Certificate',
        'epc-certificate': 'EPC Certificate',
        'gas-certificate': 'Gas Certificate',
        'inspection-report': 'Inspection Report',
        'lease-agreement': 'Lease Agreement',
        'miscellaneous': 'Miscellaneous',
        'pictures': 'Pictures',
        'property-booking-form': 'Property Booking Form',
        'property-cancellation-form': 'Property Cancellation Form',
    }
    
    TENANT_DOCS_FOLDER_SLUG = 'tenant-documents-docs'
    TENANT_DOCS_FOLDER_NAME = 'Tenant Documents'
    
    tab_data = {}
    for slug_key, human_name in document_tabs_slug_to_name_map.items():
        folder, created = Folder.objects.get_or_create(
            property=property_obj,
            name=human_name,
            parent__isnull=True
        )
        tab_data[slug_key] = {
            'folder': folder,
            'count': folder.get_document_count(),
            'human_name': human_name,
        }

    tenant_docs_root_folder, created = Folder.objects.get_or_create(
        property=property_obj,
        name=TENANT_DOCS_FOLDER_NAME,
        parent__isnull=True
    )

    if active_tab not in document_tabs_slug_to_name_map.keys() and active_tab != TENANT_DOCS_FOLDER_SLUG and active_tab != 'tenants-info':
        messages.error(request, f"Invalid section selected: '{active_tab.replace('-', ' ').title()}'. Displaying default documents.")
        return redirect('property_detail', pk=pk, active_tab='building-insurance')
    
    active_display_folder = None
    if active_tab == TENANT_DOCS_FOLDER_SLUG:
        active_display_folder = tenant_docs_root_folder
    elif active_tab in document_tabs_slug_to_name_map:
        active_display_folder = tab_data.get(active_tab, {}).get('folder')

    current_folder_pk = request.GET.get('folder_pk')
    if current_folder_pk:
        try:
            requested_subfolder = get_object_or_404(Folder, pk=current_folder_pk, property=property_obj)
            is_valid_child = False
            if active_display_folder and slugify(requested_subfolder.get_root_folder().name) == active_tab:
                is_valid_child = True
            
            if is_valid_child:
                active_display_folder = requested_subfolder
            else:
                messages.error(request, "Invalid folder access. Displaying root of current section.")
                if active_tab == TENANT_DOCS_FOLDER_SLUG:
                    active_display_folder = tenant_docs_root_folder
                elif active_tab in document_tabs_slug_to_name_map:
                    active_display_folder = tab_data.get(active_tab, {}).get('folder')

        except Exception as e:
            messages.error(request, f"Invalid folder selected: {e}. Displaying root of current section.")
            if active_tab == TENANT_DOCS_FOLDER_SLUG:
                active_display_folder = tenant_docs_root_folder
            elif active_tab in document_tabs_slug_to_name_map:
                active_display_folder = tab_data.get(active_tab, {}).get('folder')

    document_form = DocumentForm(property_instance=property_obj)
    tenant_relationship_form = TenantPropertyRelationshipForm()
    
    all_subfolders = []
    documents_in_folder = []
    if active_display_folder:
        all_subfolders = Folder.objects.filter(parent=active_display_folder).order_by('name')
        documents_in_folder = Document.objects.filter(folder=active_display_folder).order_by('uploaded_at')

    if request.method == 'POST':
        if 'file' in request.FILES:
            files = request.FILES.getlist('file')
            uploaded_count = 0
            for f in files:
                form = DocumentForm({'description': request.POST.get('description', '')}, files={'file': f}, property_instance=property_obj)
                if form.is_valid():
                    document = form.save(commit=False)
                    document.property = property_obj
                    document.folder = active_display_folder
                    document.save()
                    uploaded_count += 1
                else:
                    messages.error(request, f"Error uploading file '{f.name}': {form.errors.as_text()}")
            
            if uploaded_count > 0:
                messages.success(request, f"{uploaded_count} file(s) uploaded successfully!")
            
            redirect_url = reverse('property_detail', args=[pk, active_tab])
            if active_display_folder and active_display_folder.parent:
                return redirect(f"{redirect_url}?folder_pk={active_display_folder.pk}")
            return redirect(redirect_url)

        elif 'add_tenant_relationship' in request.POST:
            tenant_relationship_form = TenantPropertyRelationshipForm(request.POST)
            if tenant_relationship_form.is_valid():
                relationship = tenant_relationship_form.save(commit=False)
                relationship.property = property_obj
                relationship.save()
                messages.success(request, f"Tenant relationship for {relationship.tenant.full_name} added successfully!")
                return redirect('property_detail', pk=pk, active_tab='tenants-info')
            else:
                messages.error(request, "Error adding tenant relationship. Please ensure all required fields are filled correctly and dates are valid.")
                active_tab = 'tenants-info'

        elif 'delete_tenant_relationship' in request.POST:
            delete_form = TenantPropertyRelationshipDeleteForm(request.POST)
            if delete_form.is_valid():
                relationship_id = delete_form.cleaned_data['relationship_id']
                try:
                    relationship = get_object_or_404(TenantPropertyRelationship, pk=relationship_id, property=property_obj)
                    tenant_name = relationship.tenant.full_name
                    relationship.delete()
                    messages.success(request, f"Tenant relationship for {tenant_name} deleted successfully.")
                except Exception as e:
                    messages.error(request, f"Error deleting tenant relationship: {e}. It might not exist or belong to this property.")
            else:
                messages.error(request, "Invalid request to delete tenant relationship.")
            return redirect('property_detail', pk=pk, active_tab='tenants-info')

    all_tenant_relationships = property_obj.tenant_relationships.all().order_by('-move_in_date')
    current_tenants = [rel for rel in all_tenant_relationships if rel.is_current_tenant()]
    past_tenants = [rel for rel in all_tenant_relationships if not rel.is_current_tenant()]

    context = {
        'property': property_obj,
        'active_tab': active_tab,
        'document_tabs_slug_to_name_map': document_tabs_slug_to_name_map,
        'tab_data': tab_data,
        'active_display_folder': active_display_folder,
        'all_subfolders': all_subfolders,
        'documents_in_folder': documents_in_folder,
        'document_form': document_form,
        'tenant_relationship_form': tenant_relationship_form,
        'current_tenants': current_tenants,
        'past_tenants': past_tenants,
        'tenant_docs_root_folder': tenant_docs_root_folder,
        'TENANT_DOCS_FOLDER_SLUG': TENANT_DOCS_FOLDER_SLUG,
        'TENANT_INFO_SLUG': 'tenants-info',
        'current_folder_pk': current_folder_pk,
    }
    return render(request, 'website/property_detail.html', context)

@login_required
def add_folder(request, property_pk, active_tab, parent_folder_pk=None):
    property_obj = get_object_or_404(Property, pk=property_pk)
    parent_folder = None
    
    tab_slug_to_folder_name_map = {
        'building-insurance': 'Building Insurance',
        'electrical-certificate': 'Electric Certificate',
        'epc-certificate': 'EPC Certificate',
        'gas-certificate': 'Gas Certificate',
        'inspection-report': 'Inspection Report',
        'lease-agreement': 'Lease Agreement',
        'miscellaneous': 'Miscellaneous',
        'pictures': 'Pictures',
        'property-booking-form': 'Property Booking Form',
        'property-cancellation-form': 'Property Cancellation Form',
        'tenant-documents-docs': 'Tenant Documents',
    }
    
    if active_tab not in tab_slug_to_folder_name_map:
        messages.error(request, "Folders cannot be added to this section. Please select a valid document section.")
        return redirect('property_detail', pk=property_pk, active_tab='building-insurance')
    
    root_folder_name = tab_slug_to_folder_name_map.get(active_tab)

    if parent_folder_pk:
        parent_folder = get_object_or_404(Folder, pk=parent_folder_pk, property=property_obj)
    else:
        parent_folder, created = Folder.objects.get_or_create(
            property=property_obj,
            name=root_folder_name,
            parent__isnull=True
        )

    if request.method == 'POST':
        form = FolderForm(request.POST, property_instance=property_obj, parent_folder=parent_folder)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.property = property_obj
            folder.parent = parent_folder
            folder.save()
            messages.success(request, f"Folder '{folder.name}' created successfully.")
            redirect_url = reverse('property_detail', args=[property_pk, active_tab])
            if parent_folder.parent:
                return redirect(f"{redirect_url}?folder_pk={parent_folder.pk}")
            return redirect(redirect_url)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error creating folder: {error}")
    
    redirect_url = reverse('property_detail', args=[property_pk, active_tab])
    if parent_folder and parent_folder.parent:
        return redirect(f"{redirect_url}?folder_pk={parent_folder.pk}")
    return redirect(redirect_url)

@login_required
def delete_document(request, document_pk):
    document = get_object_or_404(Document, pk=document_pk)
    property_pk = document.property.pk
    tab_slug_to_folder_name_map = {
        'building-insurance': 'Building Insurance',
        'electrical-certificate': 'Electric Certificate',
        'epc-certificate': 'EPC Certificate',
        'gas-certificate': 'Gas Certificate',
        'inspection-report': 'Inspection Report',
        'lease-agreement': 'Lease Agreement',
        'miscellaneous': 'Miscellaneous',
        'pictures': 'Pictures',
        'property-booking-form': 'Property Booking Form',
        'property-cancellation-form': 'Property Cancellation Form',
        'tenant-documents-docs': 'Tenant Documents',
    }

    active_tab = 'building-insurance'
    current_folder_pk_for_redirect = None

    if document.folder:
        root_folder_of_document = document.folder.get_root_folder()
        for slug, name in tab_slug_to_folder_name_map.items():
            if name == root_folder_of_document.name:
                active_tab = slug
                break
        
        if document.folder.parent:
            current_folder_pk_for_redirect = document.folder.pk

    document.delete()
    messages.success(request, "File deleted successfully.")
    
    redirect_url = reverse('property_detail', args=[property_pk, active_tab])
    if current_folder_pk_for_redirect:
        return redirect(f"{redirect_url}?folder_pk={current_folder_pk_for_redirect}")
    return redirect(redirect_url)

@login_required
def delete_folder(request, pk):
    folder = get_object_or_404(Folder, pk=pk)
    property_id = folder.property.id
    tab_slug_to_folder_name_map = {
        'building-insurance': 'Building Insurance',
        'electrical-certificate': 'Electric Certificate',
        'epc-certificate': 'EPC Certificate',
        'gas-certificate': 'Gas Certificate',
        'inspection-report': 'Inspection Report',
        'lease-agreement': 'Lease Agreement',
        'miscellaneous': 'Miscellaneous',
        'pictures': 'Pictures',
        'property-booking-form': 'Property Booking Form',
        'property-cancellation-form': 'Property Cancellation Form',
        'tenant-documents-docs': 'Tenant Documents',
    }

    active_tab = 'building-insurance'
    root_folder = folder.get_root_folder()
    if root_folder:
        for slug, name in tab_slug_to_folder_name_map.items():
            if name == root_folder.name:
                active_tab = slug
                break
    
    redirect_folder_pk = None
    if folder.parent:
        redirect_folder_pk = folder.parent.pk
        if folder.parent.parent is None:
            redirect_folder_pk = None

    if request.method == 'POST':
        documents_to_delete = []
        folders_to_delete = [folder]
        
        while folders_to_delete:
            current_folder = folders_to_delete.pop(0)
            documents_to_delete.extend(list(current_folder.documents.all()))
            folders_to_delete.extend(list(current_folder.subfolders.all()))

        for doc in documents_to_delete:
            doc.delete()

        folder.delete()
        messages.success(request, f'Folder "{folder.name}" and all its contents deleted successfully!')
        redirect_url = reverse('property_detail', args=[property_id, active_tab])
        if redirect_folder_pk:
            return redirect(f"{redirect_url}?folder_pk={redirect_folder_pk}")
        return redirect(redirect_url)

    redirect_url = reverse('property_detail', args=[property_id, active_tab])
    if redirect_folder_pk:
        return redirect(f"{redirect_url}?folder_pk={redirect_folder_pk}")
    return redirect(redirect_url)

# ---------------------------
# New Task Views
# ---------------------------

@login_required
def tasks_list(request):
    tasks = Task.objects.all().order_by('-date_issue_reported')
    return render(request, 'tasks_list.html', {'tasks': tasks})

@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task created successfully!")
            return redirect('logbook')
        else:
            messages.error(request, "Error creating task. Please check the form.")
    else:
        form = TaskForm()
    
    return render(request, 'add_task.html', {'form': form, 'title': 'Create New Task'})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        image_form = TaskImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            new_image = image_form.save(commit=False)
            new_image.task = task
            new_image.save()
            messages.success(request, "Image uploaded successfully!")
            return redirect('task_detail', pk=pk)
        else:
            messages.error(request, "Error uploading image.")
    else:
        image_form = TaskImageForm()
    pre_inspection_images = task.images.filter(image_type='pre-inspection')
    dominic_images = task.images.filter(image_type='dominic')
    confirmation_images = task.images.filter(image_type='confirmation')
    context = {
        'task': task,
        'image_form': image_form,
        'pre_inspection_images': pre_inspection_images,
        'dominic_images': dominic_images,
        'confirmation_images': confirmation_images,
    }
    return render(request, 'task_detail.html', context)

@login_required
def edit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully!")
            return redirect('logbook')
        else:
            messages.error(request, "Error updating task.")
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'edit_task.html', {'form': form, 'title': 'Edit Task'})

@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.delete()
    messages.success(request, "Task deleted successfully.")
    return redirect('logbook')

@login_required
def delete_task_image(request, pk):
    image = get_object_or_404(TaskImage, pk=pk)
    task_pk = image.task.pk
    image.delete()
    messages.success(request, "Image deleted successfully.")
    return redirect('task_detail', pk=task_pk)

class TenantAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Record.objects.none()
        qs = Record.objects.all()
        if self.q:
            qs = qs.filter(Q(first_name__icontains=self.q) | Q(last_name__icontains=self.q))
        return qs

class PropertyAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Property.objects.none()
        qs = Property.objects.all()
        if self.q:
            qs = qs.filter(address__icontains=self.q)
        return qs