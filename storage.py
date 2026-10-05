import os
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from config import config

@dataclass
class PackageItem:
    tracking_number: str
    nickname: str = ''
    carrier: str = 'Auto'
    last_status: str = 'Unknown'
    last_description: str = 'No scan events yet'
    last_location: Optional[str] = None
    last_timestamp: Optional[str] = None
    estimated_delivery: Optional[str] = None
    is_delivered: bool = False
    snap_group: Optional[str] = None
    friend_mention: Optional[str] = None
    history: List[dict] = field(default_factory=list)
    last_checked: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

class PackageStore:
    def __init__(self, filepath: str = config.packages_file):
        self.filepath = filepath
        self.packages: Dict[str, PackageItem] = {}
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.packages[k] = PackageItem(**v)
            except Exception as e:
                print(f'[Warning] Error loading {self.filepath}: {e}')
                self.packages = {}
        else:
            self.save()

    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump({k: asdict(v) for k, v in self.packages.items()}, f, indent=2)

    def add(self, tracking_number: str, nickname: str = '', carrier: str = 'Auto', snap_group: str = None, friend_mention: str = None) -> PackageItem:
        tracking_number = tracking_number.strip()
        if tracking_number in self.packages:
            item = self.packages[tracking_number]
            if nickname: item.nickname = nickname
            if carrier and carrier != 'Auto': item.carrier = carrier
            if snap_group: item.snap_group = snap_group
            if friend_mention: item.friend_mention = friend_mention
        else:
            item = PackageItem(
                tracking_number=tracking_number,
                nickname=nickname or f'Package {tracking_number[-4:]}',
                carrier=carrier,
                snap_group=snap_group,
                friend_mention=friend_mention
            )
            self.packages[tracking_number] = item
        self.save()
        return item

    def remove(self, tracking_number: str) -> bool:
        tracking_number = tracking_number.strip()
        if tracking_number in self.packages:
            del self.packages[tracking_number]
            self.save()
            return True
        return False

    def list_all(self) -> List[PackageItem]:
        return list(self.packages.values())

    def get(self, tracking_number: str) -> Optional[PackageItem]:
        return self.packages.get(tracking_number.strip())

    def update_status(self, tracking_number: str, result: dict) -> Tuple[bool, PackageItem]:
        item = self.get(tracking_number)
        if not item:
            item = self.add(tracking_number, carrier=result.get('carrier', 'Auto'))

        new_status = result.get('status', item.last_status)
        new_desc = result.get('description', item.last_description)
        new_loc = result.get('location', item.last_location)
        new_time = result.get('timestamp', item.last_timestamp)
        new_eta = result.get('estimated_delivery', item.estimated_delivery)
        is_deliv = bool(result.get('is_delivered', False) or 'delivered' in new_status.lower() or 'delivered' in new_desc.lower())
        carrier = result.get('carrier', item.carrier)

        has_changed = (
            new_status != item.last_status or
            new_desc != item.last_description or
            (is_deliv and not item.is_delivered)
        )

        if has_changed:
            item.history.append({
                'timestamp': datetime.now().isoformat(),
                'status': new_status,
                'description': new_desc,
                'location': new_loc,
                'is_delivered': is_deliv
            })

        item.carrier = carrier
        item.last_status = new_status
        item.last_description = new_desc
        item.last_location = new_loc
        item.last_timestamp = new_time
        item.estimated_delivery = new_eta
        item.is_delivered = is_deliv
        item.last_checked = datetime.now().isoformat()

        self.save()
        return has_changed, item
