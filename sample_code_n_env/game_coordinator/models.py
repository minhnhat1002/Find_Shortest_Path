"""
Core data structures for indoor localization system
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np
import time

@dataclass
class CarState:
    """Represents the complete state of a detected car"""
    id: int
    position: np.ndarray  # (x, y) in pixels
    orientation: float    # degrees
    obstacles: List[Tuple[int, int]] = field(default_factory=list)
    position_mm: np.ndarray = None  # (x, y) in mm
    obstacles_mm: List[np.ndarray] = field(default_factory=list)
    obstacles_abs: List[Tuple[float, float]] = field(default_factory=list)  # [(distance_mm, angle_deg), ...]
    timestamp: float = None
    speed_mm_per_s: float = None
    control_command: str = 'STOP'  # e.g., 'FORWARD', 'BACKWARD', 'LEFT', 'RIGHT', 'STOP'
    control_distance: float = 0.0  # Distance to move in mm
    desired_angle: float = 0.0  # Steering angle in degrees
    route: List[Tuple[int, int]] = field(default_factory=list)
    visualized_route: List[Tuple[int, int]] = field(default_factory=list)
    numOwnedPackages: int = 0 # Number of owned package of each car
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> dict:
        """Convert CarState to dictionary for JSON serialization"""
        return {
            'id': int(self.id),
            'timestamp': self.timestamp,
            'position': [float(x) for x in self.position] if self.position is not None else None,
            'position_mm': [float(x) for x in self.position_mm] if self.position_mm is not None else None,
            'orientation': float(self.orientation) if self.orientation is not None else None,
            'speed_mm_per_s': float(self.speed_mm_per_s) if self.speed_mm_per_s is not None else None,
            'obstacles_abs': [[float(dist), float(angle)] for dist, angle in self.obstacles_abs],
            'control_command': self.control_command,
            'desired_angle': float(self.desired_angle),
            'route': [[int(x), int(y)] for x, y in self.route],
            'numOwnedPackages': self.numOwnedPackages
        }

@dataclass
class Package:
    """Represents the complete state of a detected car"""
    id: int # package ID
    position_start: List[Tuple[int, int]]  # (x, y) in mm
    position_end: np.ndarray  # (x, y) in mm
    point: int    # reward point
    ownedBy: int # Car ID 
    status: int # 0 = NEW. 1 = OWNED. 2 = FINISHED
    
    def to_dict(self) -> dict:
        """Convert CarState to dictionary for JSON serialization"""
        return {
            'id': int(self.id),
            'position_start': [(int(x), int(y)) for x, y in self.position_start],
            'position_end': [float(x) for x in self.position_end] if self.position_end is not None else None,
            'point': int(self.point),
            'ownedBy': int(self.ownedBy),
            'status': int(self.status)
        }

@dataclass
class ProcessingResult:
    """Result of processing a frame or image"""
    car_states: dict  # {car_id: CarState}
    vis_map: np.ndarray = None
    vis_camera: np.ndarray = None
    processing_time: float = None
    frame_number: int = None
    source_id: int = None
    
    def get_car_state(self, car_id: int) -> Optional[CarState]:
        """Get car state by ID"""
        return self.car_states.get(car_id)
    
    def get_all_car_states(self) -> List[CarState]:
        """Get all car states as a list"""
        return list(self.car_states.values())
    
    def to_dict(self) -> dict:
        """Convert result to dictionary"""
        return {
            'car_states': {car_id: state.to_dict() for car_id, state in self.car_states.items()},
            'processing_time': self.processing_time,
            'frame_number': self.frame_number,
            'source_id': self.source_id,
            'timestamp': time.time()
        }