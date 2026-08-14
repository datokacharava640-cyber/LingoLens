# modules/streak_system.py
import json

class StreakTracker:
    def __init__(self):
        self.streak_count = 1
        self.badges = ["🔥 Day 1 Beginner", "🎯 Early Bird"]

    def record_activity(self):
        self.streak_count += 1
        if self.streak_count == 7:
            self.badges.append("🏆 7-Day Warrior")
        return f"🔥 Current Streak: {self.streak_count} Days!\n🏅 Badges: {', '.join(self.badges)}"

    def get_status(self):
        return f"🔥 Daily Streak: {self.streak_count} Days | Unlocked Badges: {len(self.badges)}"
