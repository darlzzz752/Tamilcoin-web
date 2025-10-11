import json
import os
from typing import Set

class SubscriberManager:
    def __init__(self, filepath: str = 'subscribers.json'):
        self.filepath = filepath
        self.subscribers: Set[int] = self._load_subscribers()
    
    def _load_subscribers(self) -> Set[int]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    return set(data.get('subscribers', []))
            except Exception as e:
                print(f"Error loading subscribers: {e}")
        return set()
    
    def _save_subscribers(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump({'subscribers': list(self.subscribers)}, f, indent=2)
        except Exception as e:
            print(f"Error saving subscribers: {e}")
    
    def add_subscriber(self, user_id: int) -> bool:
        if user_id not in self.subscribers:
            self.subscribers.add(user_id)
            self._save_subscribers()
            return True
        return False
    
    def remove_subscriber(self, user_id: int) -> bool:
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self._save_subscribers()
            return True
        return False
    
    def is_subscribed(self, user_id: int) -> bool:
        return user_id in self.subscribers
    
    def get_all_subscribers(self) -> Set[int]:
        return self.subscribers.copy()
    
    def get_subscriber_count(self) -> int:
        return len(self.subscribers)
      
