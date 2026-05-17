import json
import os

import settings
from utils import app_path

class AchievementManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AchievementManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.ui = None
        self.achievements = {
            "first_room": {
                "id": "first_room",
                "name": "ach_first_room_name",
                "desc": "ach_first_room_desc",
                "easy": False, "medium": False, "hard": False
            },
            "no_damage": {
                "id": "no_damage",
                "name": "ach_no_damage_name",
                "desc": "ach_no_damage_desc",
                "easy": False, "medium": False, "hard": False
            },
            "fast_win": {
                "id": "fast_win",
                "name": "ach_fast_win_name",
                "desc": "ach_fast_win_desc",
                "easy": False, "medium": False, "hard": False
            },
            "skill_master": {
                "id": "skill_master",
                "name": "ach_skill_master_name",
                "desc": "ach_skill_master_desc",
                "easy": False, "medium": False, "hard": False
            },
            "crit_thinking": {
                "id": "crit_thinking",
                "name": "ach_crit_thinking_name",
                "desc": "ach_crit_thinking_desc",
                "easy": False, "medium": False, "hard": False
            },
            "math_god": {
                "id": "math_god",
                "name": "ach_math_god_name",
                "desc": "ach_math_god_desc",
                "easy": False, "medium": False, "hard": False
            }
        }
        self.save_file = os.path.join(app_path(), "achievements.json")
        self.load()

    def load(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r") as f:
                    data = json.load(f)
                    for ach_id, status in data.items():
                        if ach_id in self.achievements:
                            self.achievements[ach_id].update(status)
            except Exception as e:
                print(f"Error loading achievements: {e}")

    def save(self):
        try:
            data = {ach_id: {k: v for k, v in ach.items() if k in ["easy", "medium", "hard"]} 
                    for ach_id, ach in self.achievements.items()}
            with open(self.save_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving achievements: {e}")

    def unlock(self, ach_id, difficulty):
        if ach_id in self.achievements:
            if not self.achievements[ach_id].get(difficulty, False):
                # Check if this difficulty is higher than current stars
                current_stars = self.get_stars(ach_id)
                new_stars = {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 1)
                
                self.achievements[ach_id][difficulty] = True
                self.save()
                
                # Only return true if this is a "new" level of achievement (more stars)
                # or first time unlocking
                if new_stars > current_stars or current_stars == 0:
                    if self.ui:
                        self.ui.show_achievement(ach_id, difficulty)
                    return True
        return False

    def is_unlocked(self, ach_id, difficulty=None):
        if ach_id not in self.achievements:
            return False
        if difficulty:
            return self.achievements[ach_id].get(difficulty, False)
        return any([self.achievements[ach_id].get(d, False) for d in ["easy", "medium", "hard"]])

    def get_stars(self, ach_id):
        stars = 0
        if self.is_unlocked(ach_id, "easy"): stars = 1
        if self.is_unlocked(ach_id, "medium"): stars = 2
        if self.is_unlocked(ach_id, "hard"): stars = 3
        return stars

    def reset(self):
        for ach in self.achievements.values():
            ach["easy"] = False
            ach["medium"] = False
            ach["hard"] = False
        self.save()
