"""
Utility functions for analyzing patient vital signs and generating alerts.
"""
from datetime import timedelta
from django.utils import timezone
from typing import Dict, List, Optional, Any
from .models import VitalSign


# Medical thresholds for vitals alerts
VITALS_THRESHOLDS = {
    'systolic_pressure': {
        'high': 140,
        'critical_high': 180,
        'low': 90,
        'critical_low': 70,
    },
    'diastolic_pressure': {
        'high': 90,
        'critical_high': 120,
        'low': 60,
        'critical_low': 40,
    },
    'heart_rate': {
        'high': 100,
        'critical_high': 120,
        'low': 60,
        'critical_low': 40,
    },
    'temperature': {
        'high': 38.0,  # Celsius
        'critical_high': 39.5,
        'low': 35.0,
        'critical_low': 34.0,
    },
    'oxygen_saturation': {
        'low': 95,
        'critical_low': 90,
    },
    'blood_glucose': {
        'high': 140,  # mg/dL (fasting)
        'critical_high': 200,
        'low': 70,
        'critical_low': 54,
    },
    'respiratory_rate': {
        'high': 20,
        'critical_high': 30,
        'low': 12,
        'critical_low': 8,
    }
}


def analyze_vital_signs(vital_sign: VitalSign) -> List[Dict[str, Any]]:
    """
    Analyze a single vital sign reading and return alerts for abnormal values.
    
    Args:
        vital_sign: VitalSign model instance
        
    Returns:
        List of alert dictionaries with type, severity, message, and value
    """
    alerts = []
    
    # Check blood pressure
    if vital_sign.systolic_pressure and vital_sign.diastolic_pressure:
        systolic = vital_sign.systolic_pressure
        diastolic = vital_sign.diastolic_pressure
        
        if systolic >= VITALS_THRESHOLDS['systolic_pressure']['critical_high'] or \
           diastolic >= VITALS_THRESHOLDS['diastolic_pressure']['critical_high']:
            alerts.append({
                'type': 'high_bp',
                'severity': 'critical',
                'message': f'Critical high blood pressure: {systolic}/{diastolic} mmHg',
                'value': f'{systolic}/{diastolic}',
                'field': 'blood_pressure'
            })
        elif systolic >= VITALS_THRESHOLDS['systolic_pressure']['high'] or \
             diastolic >= VITALS_THRESHOLDS['diastolic_pressure']['high']:
            alerts.append({
                'type': 'high_bp',
                'severity': 'warning',
                'message': f'Elevated blood pressure: {systolic}/{diastolic} mmHg',
                'value': f'{systolic}/{diastolic}',
                'field': 'blood_pressure'
            })
        elif systolic <= VITALS_THRESHOLDS['systolic_pressure']['critical_low'] or \
             diastolic <= VITALS_THRESHOLDS['diastolic_pressure']['critical_low']:
            alerts.append({
                'type': 'low_bp',
                'severity': 'critical',
                'message': f'Critical low blood pressure: {systolic}/{diastolic} mmHg',
                'value': f'{systolic}/{diastolic}',
                'field': 'blood_pressure'
            })
        elif systolic <= VITALS_THRESHOLDS['systolic_pressure']['low'] or \
             diastolic <= VITALS_THRESHOLDS['diastolic_pressure']['low']:
            alerts.append({
                'type': 'low_bp',
                'severity': 'warning',
                'message': f'Low blood pressure: {systolic}/{diastolic} mmHg',
                'value': f'{systolic}/{diastolic}',
                'field': 'blood_pressure'
            })
    
    # Check heart rate
    if vital_sign.heart_rate:
        hr = vital_sign.heart_rate
        if hr >= VITALS_THRESHOLDS['heart_rate']['critical_high']:
            alerts.append({
                'type': 'high_hr',
                'severity': 'critical',
                'message': f'Critical high heart rate: {hr} BPM',
                'value': hr,
                'field': 'heart_rate'
            })
        elif hr >= VITALS_THRESHOLDS['heart_rate']['high']:
            alerts.append({
                'type': 'high_hr',
                'severity': 'warning',
                'message': f'Elevated heart rate: {hr} BPM',
                'value': hr,
                'field': 'heart_rate'
            })
        elif hr <= VITALS_THRESHOLDS['heart_rate']['critical_low']:
            alerts.append({
                'type': 'low_hr',
                'severity': 'critical',
                'message': f'Critical low heart rate: {hr} BPM',
                'value': hr,
                'field': 'heart_rate'
            })
        elif hr <= VITALS_THRESHOLDS['heart_rate']['low']:
            alerts.append({
                'type': 'low_hr',
                'severity': 'warning',
                'message': f'Low heart rate: {hr} BPM',
                'value': hr,
                'field': 'heart_rate'
            })
    
    # Check temperature
    if vital_sign.temperature:
        temp = vital_sign.temperature
        if temp >= VITALS_THRESHOLDS['temperature']['critical_high']:
            alerts.append({
                'type': 'fever',
                'severity': 'critical',
                'message': f'High fever: {temp}°C',
                'value': temp,
                'field': 'temperature'
            })
        elif temp >= VITALS_THRESHOLDS['temperature']['high']:
            alerts.append({
                'type': 'fever',
                'severity': 'warning',
                'message': f'Fever: {temp}°C',
                'value': temp,
                'field': 'temperature'
            })
        elif temp <= VITALS_THRESHOLDS['temperature']['critical_low']:
            alerts.append({
                'type': 'hypothermia',
                'severity': 'critical',
                'message': f'Critical low temperature: {temp}°C',
                'value': temp,
                'field': 'temperature'
            })
        elif temp <= VITALS_THRESHOLDS['temperature']['low']:
            alerts.append({
                'type': 'hypothermia',
                'severity': 'warning',
                'message': f'Low temperature: {temp}°C',
                'value': temp,
                'field': 'temperature'
            })
    
    # Check oxygen saturation
    if vital_sign.oxygen_saturation:
        o2 = vital_sign.oxygen_saturation
        if o2 <= VITALS_THRESHOLDS['oxygen_saturation']['critical_low']:
            alerts.append({
                'type': 'low_o2',
                'severity': 'critical',
                'message': f'Critical low oxygen saturation: {o2}%',
                'value': o2,
                'field': 'oxygen_saturation'
            })
        elif o2 <= VITALS_THRESHOLDS['oxygen_saturation']['low']:
            alerts.append({
                'type': 'low_o2',
                'severity': 'warning',
                'message': f'Low oxygen saturation: {o2}%',
                'value': o2,
                'field': 'oxygen_saturation'
            })
    
    # Check blood glucose
    if vital_sign.blood_glucose:
        glucose = vital_sign.blood_glucose
        if glucose >= VITALS_THRESHOLDS['blood_glucose']['critical_high']:
            alerts.append({
                'type': 'high_glucose',
                'severity': 'critical',
                'message': f'Critical high blood glucose: {glucose} mg/dL',
                'value': glucose,
                'field': 'blood_glucose'
            })
        elif glucose >= VITALS_THRESHOLDS['blood_glucose']['high']:
            alerts.append({
                'type': 'high_glucose',
                'severity': 'warning',
                'message': f'Elevated blood glucose: {glucose} mg/dL',
                'value': glucose,
                'field': 'blood_glucose'
            })
        elif glucose <= VITALS_THRESHOLDS['blood_glucose']['critical_low']:
            alerts.append({
                'type': 'low_glucose',
                'severity': 'critical',
                'message': f'Critical low blood glucose: {glucose} mg/dL',
                'value': glucose,
                'field': 'blood_glucose'
            })
        elif glucose <= VITALS_THRESHOLDS['blood_glucose']['low']:
            alerts.append({
                'type': 'low_glucose',
                'severity': 'warning',
                'message': f'Low blood glucose: {glucose} mg/dL',
                'value': glucose,
                'field': 'blood_glucose'
            })
    
    # Check respiratory rate
    if vital_sign.respiratory_rate:
        rr = vital_sign.respiratory_rate
        if rr >= VITALS_THRESHOLDS['respiratory_rate']['critical_high']:
            alerts.append({
                'type': 'high_rr',
                'severity': 'critical',
                'message': f'Critical high respiratory rate: {rr} breaths/min',
                'value': rr,
                'field': 'respiratory_rate'
            })
        elif rr >= VITALS_THRESHOLDS['respiratory_rate']['high']:
            alerts.append({
                'type': 'high_rr',
                'severity': 'warning',
                'message': f'Elevated respiratory rate: {rr} breaths/min',
                'value': rr,
                'field': 'respiratory_rate'
            })
        elif rr <= VITALS_THRESHOLDS['respiratory_rate']['critical_low']:
            alerts.append({
                'type': 'low_rr',
                'severity': 'critical',
                'message': f'Critical low respiratory rate: {rr} breaths/min',
                'value': rr,
                'field': 'respiratory_rate'
            })
        elif rr <= VITALS_THRESHOLDS['respiratory_rate']['low']:
            alerts.append({
                'type': 'low_rr',
                'severity': 'warning',
                'message': f'Low respiratory rate: {rr} breaths/min',
                'value': rr,
                'field': 'respiratory_rate'
            })
    
    return alerts


def get_vitals_summary(user_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Get a summary of patient's recent vital signs.
    
    Args:
        user_id: ID of the patient user
        days: Number of days to look back (default 7)
        
    Returns:
        Dictionary containing:
        - latest_vitals: Most recent vital sign reading
        - has_recent_vitals: Boolean indicating if vitals exist in timeframe
        - alerts: List of alerts from latest reading
        - average_values: Average values over the period
        - vitals_count: Number of readings in the period
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Get recent vitals
    recent_vitals = VitalSign.objects.filter(
        user_id=user_id,
        date_recorded__gte=cutoff_date
    ).order_by('-date_recorded')
    
    vitals_count = recent_vitals.count()
    has_recent_vitals = vitals_count > 0
    
    # Get latest vitals
    latest_vitals = recent_vitals.first()
    
    # Generate alerts from latest reading
    alerts = []
    if latest_vitals:
        alerts = analyze_vital_signs(latest_vitals)
    
    # Calculate averages
    average_values = {}
    if vitals_count > 0:
        # Calculate average heart rate
        hr_values = [v.heart_rate for v in recent_vitals if v.heart_rate]
        if hr_values:
            average_values['heart_rate'] = round(sum(hr_values) / len(hr_values), 1)
        
        # Calculate average blood pressure
        systolic_values = [v.systolic_pressure for v in recent_vitals if v.systolic_pressure]
        diastolic_values = [v.diastolic_pressure for v in recent_vitals if v.diastolic_pressure]
        if systolic_values:
            average_values['systolic_pressure'] = round(sum(systolic_values) / len(systolic_values), 1)
        if diastolic_values:
            average_values['diastolic_pressure'] = round(sum(diastolic_values) / len(diastolic_values), 1)
        
        # Calculate average temperature
        temp_values = [v.temperature for v in recent_vitals if v.temperature]
        if temp_values:
            average_values['temperature'] = round(sum(temp_values) / len(temp_values), 1)
        
        # Calculate average oxygen saturation
        o2_values = [v.oxygen_saturation for v in recent_vitals if v.oxygen_saturation]
        if o2_values:
            average_values['oxygen_saturation'] = round(sum(o2_values) / len(o2_values), 1)
        
        # Calculate average blood glucose
        glucose_values = [v.blood_glucose for v in recent_vitals if v.blood_glucose]
        if glucose_values:
            average_values['blood_glucose'] = round(sum(glucose_values) / len(glucose_values), 1)
    
    # Serialize latest vitals
    latest_vitals_data = None
    if latest_vitals:
        from .serializers import VitalSignSerializer
        latest_vitals_data = VitalSignSerializer(latest_vitals).data
    
    return {
        'latest_vitals': latest_vitals_data,
        'has_recent_vitals': has_recent_vitals,
        'alerts': alerts,
        'average_values': average_values,
        'vitals_count': vitals_count,
        'days_range': days,
    }
