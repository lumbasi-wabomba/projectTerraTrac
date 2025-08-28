from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis_models


# Create your models here.
class CustomUser(AbstractUser):
    pass
    
class ForestArea(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    geo_location = gis_models.PointField()
    description = models.TextField()
    last_ndvi = models.FloatField()
    date_checked = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class NDVIRecord(models.Model):
    forest_area = models.ForeignKey(ForestArea, on_delete=models.CASCADE, related_name='forest_NDVI', db_index=True)
    ndvi_value = models.FloatField()
    image_date = models.DateField(auto_created=True)
    image_url = models.URLField(max_length=500)

    def __str__(self):
        return self.forest_area
    
class Alert(models.Model):
    forest_area = models.ForeignKey(ForestArea, on_delete=models.CASCADE, related_name='forest_alert', db_index=True)
    ALERT_TYPE_CHOICES ={
        ('afforestation', 'Afforestation'),
        ('deforestation', 'Deforestation')
    }
    alert_type = models.CharField(choices=ALERT_TYPE_CHOICES, db_index=True, max_length=100)
    change_value = models.FloatField()
    triggered_on = models.DateTimeField(auto_created=True)
    STATUS_CHOICES = {
        ('verified', 'Verified'),
        ('pending', 'Pending')
        ('rejected', 'Rejected')
    }
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, db_index=True)

    def __str__(self):
        return self.alert_type
    
class CommunityReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reporter_reports')
    image_url = models.URLField(max_length=500)
    geo_location = gis_models.PointField()
    descritption = models.TextField()
    submitted_on = models.DateField(auto_created=True)
    linked_alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='has_alerts', db_index=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return super().__str__()
    
class Verification(models.Model):
    verifier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_verifiers')
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='to_be_verified', db_index=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField()
    timestamp = models.DateTimeField(auto_created=True)

    def __str__(self):
        return self.is_verified

