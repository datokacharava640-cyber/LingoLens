# modules/referral_system.py
import random
import string

class ReferralEngine:
    def __init__(self):
        self.referral_code = "LINGO-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self.invited_count = 0

    def get_invite_info(self):
        return f"🎁 Your Invite Code: [b]{self.referral_code}[/b]\n👥 Friends Invited: {self.invited_count}\n💡 Invite 2 friends to unlock Offline & Premium Voices!"

    def simulate_friend_joined(self):
        self.invited_count += 1
        return f"🎉 Friend joined using code {self.referral_code}! Total invited: {self.invited_count}"
