from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select
from app.models import DailyHealthStats, HealthInsight

def generate_insights(username: str, current_stats: DailyHealthStats, session: Session) -> List[HealthInsight]:
    """
    Analyzes the user's latest daily stats against history to generate insights.
    """
    insights = []
    
    # 1. Anomaly Detection: Heart Rate
    if current_stats.avg_heart_rate > 100:
        insights.append(HealthInsight(
            username=username,
            type="Anomaly",
            severity="WARNING",
            message=f"Your average heart rate today was high ({current_stats.avg_heart_rate:.1f} bpm). Resting heart rates above 100 bpm may indicate stress or other issues."
        ))
    
    # 2. Anomaly Detection: Sleep
    if current_stats.sleep_hours > 0 and current_stats.sleep_hours < 6:
        insights.append(HealthInsight(
            username=username,
            type="Recommendation",
            severity="INFO",
            message=f"You only slept {current_stats.sleep_hours} hours. Adequate sleep (7-9 hours) is crucial for recovery."
        ))

    # 3. Achievement: Steps
    if current_stats.total_steps >= 10000:
        insights.append(HealthInsight(
            username=username,
            type="Achievement",
            severity="INFO",
            message="Great job! You hit 10,000 steps today. Keep staying active!"
        ))
    elif current_stats.total_steps < 1000:
         insights.append(HealthInsight(
            username=username,
            type="Motivation",
            severity="INFO",
            message="You've been quite sedentary today (<1000 steps). Try taking a short walk."
        ))

    # 4. Trend Analysis (Simple: Compare with yesterday)
    yesterday = current_stats.date - timedelta(days=1)
    statement = select(DailyHealthStats).where(
        DailyHealthStats.username == username, 
        DailyHealthStats.date == yesterday
    )
    yesterday_stats = session.exec(statement).first()
    
    if yesterday_stats:
        # Steps Trend
        if current_stats.total_steps > yesterday_stats.total_steps * 1.2:
             insights.append(HealthInsight(
                username=username,
                type="Trend",
                severity="INFO",
                message="Your activity levels are trending up! You walked 20% more than yesterday."
            ))
        
    
    return insights

def generate_summary_text(username: str, session: Session) -> str:
    """
    Generates a narrative summary based on the last 7 days of data.
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)
    
    statement = select(DailyHealthStats).where(
        DailyHealthStats.username == username,
        DailyHealthStats.date >= start_date
    ).order_by(DailyHealthStats.date.asc())
    
    stats = session.exec(statement).all()
    
    if not stats:
        return "Not enough data to generate a summary for this week. Start logging your health metrics!"
        
    days_logged = len(stats)
    total_steps = sum(s.total_steps for s in stats)
    avg_steps = total_steps / days_logged if days_logged else 0
    
    total_sleep = sum(s.sleep_hours for s in stats)
    avg_sleep = total_sleep / days_logged if days_logged else 0
    
    avg_hr = sum(s.avg_heart_rate for s in stats if s.avg_heart_rate > 0)
    hr_days = sum(1 for s in stats if s.avg_heart_rate > 0)
    final_avg_hr = avg_hr / hr_days if hr_days else 0
    
    # Narrative Generation
    parts = [f"Health Summary for the last {days_logged} days:"]
    
    # Activity
    if avg_steps > 10000:
        parts.append(f"You've been incredibly active, averaging {int(avg_steps)} steps/day. Excellent work!")
    elif avg_steps > 7000:
        parts.append(f"Your activity level is good, with an average of {int(avg_steps)} steps/day.")
    else:
        parts.append(f"Your activity is on the lower side ({int(avg_steps)} avg steps). Try to aim for 7,000+ daily.")
        
    # Sleep
    if avg_sleep >= 7:
        parts.append(f"Your sleep hygiene is great, averaging {avg_sleep:.1f} hours.")
    elif avg_sleep >= 5:
        parts.append(f"You're averaging {avg_sleep:.1f} hours of sleep. Try to get a bit more rest.")
    else:
        parts.append(f"Your sleep is quite low ({avg_sleep:.1f}h avg). Prioritize recovery this week.")
        
    # Heart Rate
    if final_avg_hr > 0:
        if final_avg_hr < 80:
             parts.append(f"Your average heart rate is healthy at {int(final_avg_hr)} bpm.")
        else:
             parts.append(f"Your average heart rate ({int(final_avg_hr)} bpm) is a bit high. Watch out for stress.")
             
    return " ".join(parts)
