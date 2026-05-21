from altinet.home.models import (
    DevicePlacement,
    Door,
    Floor,
    HomeModel,
    HouseDimensions,
    Light,
    PerceptionPodPlacement,
    PropertyBoundary,
    Room,
    RoomRegion,
    Wall,
)


def create_default_home_model() -> HomeModel:
    room = Room(id="room-demo", floor_id="floor-ground", name="Demo Room", x=0.0, y=0.0, width=6.0, depth=4.0)
    walls = [
        Wall(id="wall-north", room_id=room.id, floor_id=room.floor_id, x1=0.0, y1=0.0, x2=6.0, y2=0.0),
        Wall(id="wall-east", room_id=room.id, floor_id=room.floor_id, x1=6.0, y1=0.0, x2=6.0, y2=4.0),
        Wall(id="wall-south", room_id=room.id, floor_id=room.floor_id, x1=6.0, y1=4.0, x2=0.0, y2=4.0),
        Wall(id="wall-west", room_id=room.id, floor_id=room.floor_id, x1=0.0, y1=4.0, x2=0.0, y2=0.0),
    ]
    light = Light(id="light-demo-1", room_id=room.id, floor_id=room.floor_id, name="Demo Ceiling Light", x=3.0, y=2.0)
    return HomeModel(
        property_name="Altinet Demo Property",
        property_boundary=PropertyBoundary(width=20.0, depth=30.0),
        house_dimensions=HouseDimensions(width=6.0, depth=4.0),
        floors=[Floor(id="floor-ground", name="Ground Floor", level=0), Floor(id="floor-1", name="Floor 1", level=1)],
        rooms=[room],
        room_regions=[RoomRegion(id="region-demo-room", floor_id=room.floor_id, name=room.name, points=[[0.0, 0.0], [6.0, 0.0], [6.0, 4.0], [0.0, 4.0]])],
        walls=walls,
        doors=[Door(id="door-main", room_id=room.id, floor_id=room.floor_id, wall_id="wall-south", x=2.4, y=4.0, width=0.9)],
        windows=[],
        lights=[light],
        perception_pods=[
            PerceptionPodPlacement(
                id="pod-demo-1",
                name="Pod 1",
                floor_id=room.floor_id,
                x=1.0,
                y=1.0,
                orientation_degrees=45,
                camera_enabled=True,
                microphone_enabled=True,
                sensors=["camera", "microphone", "motion"],
            )
        ],
        device_placements=[DevicePlacement(id="placement-light-demo-1", device_id=light.id, room_id=room.id, x=light.x, y=light.y)],
        units="metres",
    )
