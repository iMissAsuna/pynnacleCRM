# website/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # General Views
    path('', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logbook/', views.logbook, name='logbook'), # Keep this URL
    path('maintenance/', views.maintenance, name='maintenance'),
    path('certificates/', views.certificates, name='certificates'),
    path('archive/', views.archive, name='archive'),
    path('keys_register/', views.keys_register, name='keys_register'),
    path('cleaning/', views.cleaning, name='cleaning'),

    # Tenant Views
    path('tenants/', views.tenants_list, name='tenants_list'),
    path('tenants/add/', views.add_record, name='add_record'),
    path('tenants/<int:pk>/', views.tenant_record, name='record'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),

    # Property Views
    path('properties/', views.properties_list, name='properties_list'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/edit/<int:pk>/', views.edit_property, name='edit_property'),
    path('properties/delete/<int:pk>/', views.delete_property, name='delete_property'),
    path('properties/<int:pk>/<slug:active_tab>/', views.property_detail, name='property_detail'),
    path('documents/delete/<int:document_pk>/', views.delete_document, name='delete_document'),
    path('folders/add/<int:property_pk>/<slug:active_tab>/', views.add_folder, name='add_folder'),
    path('folders/add/<int:property_pk>/<slug:active_tab>/<int:parent_folder_pk>/', views.add_folder, name='add_subfolder'),
    path('folders/delete/<int:pk>/', views.delete_folder, name='delete_folder'),

    # New Task Views
    path('tasks/', views.tasks_list, name='tasks_list'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/edit/<int:pk>/', views.edit_task, name='edit_task'),
    path('tasks/delete/<int:pk>/', views.delete_task, name='delete_task'),
    path('tasks/images/delete/<int:pk>/', views.delete_task_image, name='delete_task_image'),
    path('tenant-autocomplete/', views.TenantAutocomplete.as_view(), name='tenant-autocomplete'),
    path('property-autocomplete/', views.PropertyAutocomplete.as_view(), name='property-autocomplete'),
]