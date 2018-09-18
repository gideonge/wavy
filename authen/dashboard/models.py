from django.db import models

CHOICE_OPTIONS = ((True, "Yes"), (False, 'No'))

# Create your models here.
class TestBo(models.Model):
    checkbox = models.BooleanField(choices=CHOICE_OPTIONS)
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name