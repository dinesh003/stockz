import datetime
import numpy as np

def time_to_minutes(time_str):
    """Convert HH:MM to minutes from midnight."""
    try:
        t = datetime.datetime.strptime(time_str.strip(), "%H:%M").time()
        return t.hour * 60 + t.minute
    except ValueError:
        # Fallback if there is a seconds part or dates
        try:
            # Try parsing timestamp
            if " " in time_str:
                time_part = time_str.split(" ")[1]
            elif "T" in time_str:
                time_part = time_str.split("T")[1]
            else:
                time_part = time_str
            # Extract HH:MM
            parts = time_part.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return 0

def minutes_to_time_str(minutes):
    """Convert minutes from midnight to HH:MM string."""
    minutes = int(round(minutes))
    hour = (minutes // 60) % 24
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"

def calculate_median_time(time_list):
    """Calculate the median time from a list of HH:MM strings."""
    if not time_list:
        return "N/A"
    minutes_list = [time_to_minutes(t) for t in time_list if t and t != "N/A"]
    if not minutes_list:
        return "N/A"
    median_minutes = np.median(minutes_list)
    return minutes_to_time_str(median_minutes)
