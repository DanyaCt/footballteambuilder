from django.db import models

class Country(models.Model):
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.country
    
    class Meta:
        verbose_name_plural = "Countries"

class Player(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    age = models.IntegerField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    experience = models.IntegerField()
    rank = models.IntegerField()

    def __str__(self):
        return f"{self.name} {self.surname}"
