from django.db import models
import uuid # For potential use if not using default auto-incrementing IDs

class FlightArrival(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Alternative PK
    flight_number = models.CharField(max_length=20)
    airline_name = models.CharField(max_length=100, null=True, blank=True)
    origin_airport_code = models.CharField(max_length=10) # IATA or ICAO
    origin_city = models.CharField(max_length=100, null=True, blank=True)
    scheduled_arrival_dt = models.DateTimeField()
    actual_arrival_dt = models.DateTimeField(null=True, blank=True)
    aircraft_type = models.CharField(max_length=50, null=True, blank=True) # e.g., A320, B738
    estimated_passengers = models.IntegerField(null=True, blank=True)
    data_source = models.CharField(max_length=50, null=True, blank=True) # To track where data came from
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['scheduled_arrival_dt']),
            models.Index(fields=['flight_number']),
        ]
        # To prevent duplicate entries for the same flight on the same day from the same source
        unique_together = ('flight_number', 'scheduled_arrival_dt', 'data_source')

    def __str__(self):
        return f"{self.airline_name} {self.flight_number} from {self.origin_airport_code} on {self.scheduled_arrival_dt.strftime('%Y-%m-%d')}"

class CruiseArrival(models.Model):
    ship_name = models.CharField(max_length=100)
    cruise_line_name = models.CharField(max_length=100, null=True, blank=True)
    scheduled_arrival_date = models.DateField()
    scheduled_arrival_time = models.TimeField(null=True, blank=True)
    scheduled_departure_date = models.DateField(null=True, blank=True)
    scheduled_departure_time = models.TimeField(null=True, blank=True)
    passenger_capacity_double = models.IntegerField(null=True, blank=True) # Standard capacity
    estimated_passengers = models.IntegerField(null=True, blank=True)
    data_source = models.CharField(max_length=50, null=True, blank=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['scheduled_arrival_date']),
            models.Index(fields=['ship_name']),
        ]
        unique_together = ('ship_name', 'scheduled_arrival_date', 'data_source')

    def __str__(self):
        return f"{self.ship_name} arriving on {self.scheduled_arrival_date}"

class DailyWeather(models.Model):
    """Stores daily weather forecast for a specific location, e.g., Isla Verde."""
    forecast_date = models.DateField()
    location_name = models.CharField(max_length=100, default="Isla Verde") # Could be enum or FK later
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    sunrise_time = models.TimeField(null=True, blank=True)
    sunset_time = models.TimeField(null=True, blank=True)
    # Store detailed hourly forecasts as a JSON array of objects
    # Each object: {time_epoch, time_str, temp_c, temp_f, precip_prob_percent, precip_mm, wind_speed_kmh, condition_code, short_desc}
    hourly_forecasts = models.JSONField(default=list)
    daily_condition_summary = models.CharField(max_length=255, null=True, blank=True) # e.g., "Sunny with afternoon showers"
    daily_temp_max_c = models.FloatField(null=True, blank=True)
    daily_temp_min_c = models.FloatField(null=True, blank=True)
    daily_avg_precip_prob = models.FloatField(null=True, blank=True) # Average probability over daylight hours
    daily_total_precip_mm = models.FloatField(null=True, blank=True) # Total precipitation over 24h or daylight
    data_source = models.CharField(max_length=50, null=True, blank=True) # e.g., NWS API
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['forecast_date', 'location_name']),
        ]
        unique_together = ('forecast_date', 'location_name', 'data_source') # One forecast per location per source per day

    def __str__(self):
        return f"Weather for {self.location_name} on {self.forecast_date}"

class DailyTouristSummary(models.Model):
    """Aggregated daily metrics used as input for predictions."""
    summary_date = models.DateField(unique=True)
    total_estimated_flight_passengers = models.IntegerField(default=0)
    total_estimated_cruise_passengers = models.IntegerField(default=0)
    # Could add other indicators like hotel_occupancy_proxy if available
    overall_tourist_pressure_index = models.FloatField(null=True, blank=True) # A calculated index
    # FK to DailyWeather or store key weather attributes directly
    weather_summary_fk = models.OneToOneField(DailyWeather, on_delete=models.SET_NULL, null=True, blank=True, related_name="tourist_summary")
    day_type = models.CharField(max_length=20, null=True, blank=True) # e.g., Weekday, Weekend, Holiday_PR
    calculated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tourist Summary for {self.summary_date}"

class BeachAttendancePrediction(models.Model):
    """Stores the output of the beach attendance prediction model."""
    prediction_date = models.DateField() # The date for which the prediction is made
    # FK to DailyTouristSummary to link prediction to its input features
    tourist_summary_fk = models.OneToOneField(DailyTouristSummary, on_delete=models.CASCADE, related_name="beach_prediction")
    probability_score = models.FloatField() # Value between 0.0 and 1.0
    prediction_category = models.CharField(max_length=20, null=True, blank=True) # e.g., Low, Medium, High
    # Store the exact features used for this prediction for auditability and model retraining
    input_features_json = models.JSONField(default=dict)
    model_version = models.CharField(max_length=50, null=True, blank=True) # Version of the model used
    predicted_at = models.DateTimeField(auto_now_add=True) # When the prediction was generated

    class Meta:
        indexes = [
            models.Index(fields=['prediction_date']),
        ]
        unique_together = ('prediction_date', 'model_version') # Allow multiple model versions for same day if needed

    def __str__(self):
        return f"Beach Prediction for {self.prediction_date}: {self.probability_score:.2f}"
