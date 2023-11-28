from django.db import models
from django.utils.timezone import localtime
import uuid
from django.contrib.auth.models import User
from tenant_schemas.models import TenantMixin
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.admin import AdminSite

# Create your models here.


class TenantUser(AbstractUser):
    # Add any additional fields here if needed


    def __str__(self):
        return self.first_name + ' ' + self.last_name

    pass




GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until =  models.DateField()
    on_trial = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    def __str__(self):
        return self.name
class Student(models.Model):

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    gender = models.CharField(max_length=16, choices=GENDER_CHOICES)
    user_id = models.UUIDField(default=uuid.uuid4, editable=True)
    homeroom_teacher = models.ForeignKey(TenantUser, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Ban(models.Model):
    first_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="First Student+")
    second_student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="Second Student+")

    def __str__(self):
        return f"{self.first_student} and {self.second_student}"

class PassRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField()
    details = models.TextField()
    in_or_out = models.CharField(max_length=3)
    open = models.BooleanField()
    teacher = models.ForeignKey(TenantUser, on_delete=models.CASCADE)


    def __str__(self):
        formatted_date = localtime(self.date).strftime("%B %-d, %I:%M %p").lower()
        return f"{self.student} on {formatted_date}"

class HallwayCapacity(models.Model):
    gender = models.CharField(max_length=16, choices=GENDER_CHOICES)
    limit = models.IntegerField(help_text="Maximum number of students allowed in the hallway at a time, of a given gender.")

    class Meta:
        verbose_name = "Hallway Capacity"
        verbose_name_plural = "Hallway Capacities"  # Correct plural form

    def __str__(self):
        return f"Maximum Allowed {self.gender}s in the hallway."