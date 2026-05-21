from __future__ import annotations

from pathlib import Path

from altinet.domain.agents import AgentProfile
from altinet.domain.devices import DeviceProfile
from altinet.domain.home import HomeProfile
from altinet.store.json_store import JsonStore
from altinet.store.repositories.users_repository import UsersRepository


class RegistryService:
    def __init__(self, base_dir: Path = Path("data/altinet")):
        self.users = UsersRepository(base_dir / "users" / "users.json")
        self.home_store = JsonStore(base_dir / "home" / "home.json")
        self.agent_store = JsonStore(base_dir / "agents" / "agents.json")
        self.device_store = JsonStore(base_dir / "devices" / "devices.json")

    def load_registry(self) -> dict:
        return {
            "users": [u.model_dump(mode="json") for u in self.users.list_users()],
            "home": self.home_store.load({"home": HomeProfile(name="Altinet Home").model_dump(mode="json")}),
            "agents": self.agent_store.load({"agents": []}),
            "devices": self.device_store.load({"devices": []}),
        }

    def save_home(self, home: HomeProfile) -> None:
        self.home_store.save({"home": home.model_dump(mode="json")})

    def save_agents(self, agents: list[AgentProfile]) -> None:
        self.agent_store.save({"agents": [a.model_dump(mode="json") for a in agents]})

    def save_devices(self, devices: list[DeviceProfile]) -> None:
        self.device_store.save({"devices": [d.model_dump(mode="json") for d in devices]})
