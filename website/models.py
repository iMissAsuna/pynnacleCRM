from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
import datetime
import logging

class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='custom_user',
    )

# --- Record & Tenant-related Models ---
class Record(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=50, default="")
    county = models.CharField(max_length=50, default="")
    postcode = models.CharField(max_length=10)
    next_of_kin = models.CharField(max_length=50, blank=True, null=True)
    move_in_date = models.DateField(default=datetime.date.today)
    key_collection = models.DateField(default=datetime.date.today)
    move_out_date = models.DateField(blank=True, null=True)
    key_drop_off = models.DateField(blank=True, null=True)
    current_residence = models.CharField(max_length=255, default="Unknown")
    
    OCCUPANCY_CHOICES = [
        ('Vacant', 'Vacant'),
        ('Occupied', 'Occupied'),
        ('Previous', 'Previous')
    ]
    occupancy_status = models.CharField(
        max_length=50,
        choices=OCCUPANCY_CHOICES,
        default='Vacant'
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tenant_image_upload_to(self, filename):
        tenant_folder_name = slugify(f"{self.first_name}-{self.last_name}-{self.pk}")
        return os.path.join('tenant_documents', tenant_folder_name, filename)

class TenantImage(models.Model):
    CATEGORY_CHOICES = [
        ('move_in', 'Move-in Photos'),
        ('move_out', 'Move-out Photos'),
        ('id_photo', 'ID Documents'),
        ('other', 'Other Documents'),
    ]

    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='tenant_images/%Y/%m/%d/')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.record.first_name} {self.record.last_name} - {self.get_category_display()}"
    
    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

# --- Property & Document Management Models ---

class Property(models.Model):
    PROPERTY_TYPES = [
        ('one_bedroom', '1 Bedroom'),
        ('two_bedroom', '2 Bedroom'),
        ('three_bedroom', '3 Bedroom'),
        ('studio', 'Studio'),
        ('flat', 'Flat'),
        ('house', 'House'),
        ('block', 'Block'),
    ]

    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255, help_text="Street address")
    postcode = models.CharField(max_length=10)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    number_of_units = models.IntegerField(default=1)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    building_insurance_expiry_date = models.DateField(null=True, blank=True)
    gas_certificate_expiry_date = models.DateField(null=True, blank=True)
    electric_certificate_expiry_date = models.DateField(null=True, blank=True)
    epc_certificate_expiry_date = models.DateField(null=True, blank=True)
    fra_certificate_expiry_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Set up logger
logger = logging.getLogger(__name__)

class PropertyMedia(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='property_media/%Y/%m/%d/')
    category = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.file.name)

    def delete(self, *args, **kwargs):
        try:
            if self.file:
                self.file.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting PropertyMedia file {self.file.name}: {str(e)}")
        super().delete(*args, **kwargs)

class Folder(models.Model):
    name = models.CharField(max_length=255)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')

    class Meta:
        unique_together = ('name', 'property', 'parent')

    def __str__(self):
        return self.name

    def get_document_count(self):
        count = self.documents.count()
        for subfolder in self.subfolders.all():
            count += subfolder.get_document_count()
        return count
    
    def get_root_folder(self):
        if not self.parent:
            return self
        return self.parent.get_root_folder()
    
    def get_full_path(self):
        path = [self.name]
        current_folder = self
        while current_folder.parent:
            current_folder = current_folder.parent
            path.append(current_folder.name)
        return ' / '.join(reversed(path))

class Document(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    file = models.FileField(upload_to='property_documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.file.name)
    
    def save(self, *args, **kwargs):
        if self.folder and not self.property:
            self.property = self.folder.property
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

# --- New Models for Tasks ---

class Task(models.Model):
    JOB_ALLOCATED_CHOICES = [
        ('Waleed', 'Waleed'),
        ('Nadeem', 'Nadeem'),
        ('Ruth', 'Ruth'),
        ('Sheraz', 'Sheraz'),
        ('Other', 'Other'),
    ]

    job_id = models.CharField(max_length=50, unique=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tasks')
    tenant = models.ForeignKey(Record, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    date_issue_reported = models.DateField()
    description_of_issue = models.TextField()
    job_allocated = models.CharField(max_length=50, choices=JOB_ALLOCATED_CHOICES, blank=True)
    date_completed = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.job_id} - {self.description_of_issue[:30]}"

class TaskImage(models.Model):
    TASK_IMAGE_TABS = [
        ('pre-inspection', 'Pre-Inspection'),
        ('dominic', 'Dominic'),
        ('confirmation', 'Confirmation'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='task_images/')
    image_type = models.CharField(max_length=20, choices=TASK_IMAGE_TABS)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.task.job_id} ({self.image_type})"

# Signal to delete image file when TaskImage instance is deleted
@receiver(post_delete, sender=TaskImage)
def auto_delete_file_on_delete_task_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

# --- New Model for Tenant-Property Relationships ---
class TenantPropertyRelationship(models.Model):
    tenant = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='property_relationships')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tenant_relationships')
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('tenant', 'property', 'move_in_date')

    def __str__(self):
        status = "Current" if self.is_current_tenant() else "Past"
        return f"{self.tenant.full_name} at {self.property.name} ({status})"

    def is_current_tenant(self):
        return self.move_out_date is None or self.move_out_date >= datetime.date.today()