# Indoor Localization System

A complete Python package for real-time indoor localization using ArUco markers with obstacle detection, HTTP API, and advanced visualization features.

## Quick Start

**New to the package?** Start with `main.py` in the main directory for a quick demo.

**Want to learn more?** Use `example_usage.py` for comprehensive examples and tutorials.

**Need integration help?** See `EXAMPLE_FILES_GUIDE.md` for detailed guidance on which files to use.

## Features

- Real-time car detection and tracking using ArUco markers
- Obstacle detection with configurable scan radius
- Position calculation in real-world coordinates (mm)
- Speed calculation based on position history
- HTTP REST API for accessing car states
- Support for multiple input sources (images, videos, cameras)
- **Advanced visualization with aspect ratio preservation**
- **Configurable window sizing based on screen resolution**
- **Smooth anti-aliased rendering for professional appearance**
- Thread-safe processing with CORS-enabled API
- **Resizable windows that maintain proper image proportions**

## Installation

1. Ensure you have the required dependencies:
```bash
pip install opencv-python numpy
```

2. Copy the `indoor_localization` package to your project directory.

## Quick Start

### Basic Usage

```python
from indoor_localization import create_system, InputSource

# Create system with minimal configuration
system = create_system(
    map_path='city_map.png',
    car_marker_ids=[10, 11, 12]
)

# Start API server
system.start_api_server()

# Process single image
result = system.process_image_file('camera_image.png')
print(f"Cars detected: {len(result.car_states)}")

# Real-time processing
sources = [InputSource('camera', source_id=0)]
system.start_video_processing(sources, enable_display=True)
```

### Advanced Configuration

```python
from indoor_localization import LocalizationConfig, IndoorLocalizationSystem

config = LocalizationConfig(
    map_path='city_map.png',
    aruco_marker_size_mm=15.0,
    car_width_mm=20.0,
    car_length_mm=20.0,
    scan_radius_mm=50.0,
    screen_display_height=1200,  # Configure display window sizing
    reference_markers={
        0: (65, 65),
        1: (3183, 65),
        2: (3183, 2209),
        3: (65, 2209)
    },
    car_marker_ids=[10, 11, 12],
    server_port=8080
)

system = IndoorLocalizationSystem(config)
```

## API Endpoints

Once the system is running, the following HTTP endpoints are available:

- `GET /health` - System health check
- `GET /cars` - Get all car states
- `GET /car/{car_id}` - Get specific car state

### Example API Response

```json
{
  "id": 10,
  "timestamp": 1642678901.234,
  "position_mm": [150.5, 200.3],
  "orientation": 45.2,
  "speed_mm_per_s": 120.5,
  "obstacles_abs": [
    [25.3, 30.0],
    [45.1, -15.2]
  ]
}
```

## Input Sources

### Images
```python
# Single image
result = system.process_image_file('image.png')

# Multiple images
results = system.process_image_files(['img1.png', 'img2.png'])
```

### Video Files
```python
sources = [InputSource('video', source_path='video.mp4')]
system.start_video_processing(sources)
```

### Cameras
```python
sources = [
    InputSource('camera', source_id=0),  # Default camera
    InputSource('camera', source_id=1)   # Secondary camera
]
system.start_video_processing(sources)
```

## Display and Visualization Features

### Advanced Window Management
The system provides professional-quality visualization with several advanced features:

#### Aspect Ratio Preservation
- **Automatic aspect ratio maintenance** when resizing windows
- **Centered image display** with black borders when needed
- **Works with manual resizing and window maximization**

#### Screen-Adaptive Sizing
```python
config = LocalizationConfig(
    screen_display_height=1200,  # Base resolution for window sizing
    # Windows automatically scale to this height
)
```

#### Window Features
- **Resizable windows** that maintain image proportions
- **Grid layout** for multiple camera sources
- **Professional anti-aliased rendering** for smooth lines and curves
- **Consistent sizing** across different monitor resolutions

### Visualization Controls
```python
# Reset all windows to default sizes
system.reset_window_sizes()

# Process with display enabled/disabled
system.start_video_processing(sources, enable_display=True)
```

### Window Layout
- **Combined Map View**: Shows all cars from all sources with coordinate system
- **Individual Source Windows**: Each camera/video gets its own window
- **Automatic positioning**: Windows arranged in a grid layout
- **Source color coding**: Each source gets a unique color for easy identification

## Callbacks

Set up callbacks to respond to events:

```python
def on_car_detected(car_state):
    print(f"New car detected: {car_state.id}")

def on_car_lost(car_id):
    print(f"Car lost: {car_id}")

def on_frame_processed(result):
    print(f"Frame {result.frame_number} processed")

system.on_car_detected = on_car_detected
system.on_car_lost = on_car_lost
system.on_frame_processed = on_frame_processed
```

## Configuration Options

### LocalizationConfig Parameters

#### Core Processing
- `aruco_dict`: ArUco dictionary type (default: cv2.aruco.DICT_4X4_50)
- `aruco_marker_size_mm`: Real-world marker size in mm
- `car_width_mm`: Car width for obstacle marking
- `car_length_mm`: Car length for obstacle marking
- `reference_markers`: Dictionary of reference marker positions
- `car_marker_ids`: List of ArUco IDs used for cars
- `map_path`: Path to the map image file
- `scan_radius_mm`: Obstacle detection radius in mm

#### Display and Visualization
- `screen_display_height`: Base height for window sizing in pixels (default: 1000)
  - **Map windows**: Set to `screen_display_height // 2`
  - **Camera windows**: Set to `screen_display_height // 3`
  - **All windows maintain 4:3 aspect ratio**

#### Network and Server
- `server_port`: HTTP API server port
- `server_host`: HTTP API server host (default: '0.0.0.0')

#### Advanced Settings
- `coordinate_origin_offset_mm`: Coordinate system offset (default: (12.5, 12.5))
- `max_position_history_length`: Position history buffer size for speed calculation

## System Statistics

Get real-time system statistics:

```python
stats = system.get_statistics()
print(f"FPS: {stats['average_fps']:.1f}")
print(f"Active cars: {stats['active_cars']}")
print(f"Runtime: {stats['runtime_seconds']:.1f}s")
```

## Display Best Practices

### Screen Resolution Optimization
```python
# For 1080p monitors
config.screen_display_height = 1000

# For 1440p monitors
config.screen_display_height = 1200

# For 4K monitors
config.screen_display_height = 1600
```

### Window Management Tips
- **Resize by dragging**: Windows maintain aspect ratio automatically
- **Maximize windows**: Image centers with black borders if needed
- **Multiple monitors**: Works across different screen sizes
- **Reset anytime**: Call `system.reset_window_sizes()` to restore defaults

### Performance Considerations
- **Disable display for production**: Set `enable_display=False` for better performance
- **Lower resolution**: Reduce `screen_display_height` for older hardware
- **Background processing**: Display rendering runs in separate thread

## Error Handling

The system includes robust error handling:

```python
try:
    result = system.process_image_file('nonexistent.png')
except FileNotFoundError as e:
    print(f"Image not found: {e}")

try:
    system.start_video_processing(sources)
except Exception as e:
    print(f"Processing error: {e}")
finally:
    system.stop_api_server()
```

## Integration Example

```python
import requests
import json
from indoor_localization import create_system, InputSource

# Start system
system = create_system(map_path='map.png', car_marker_ids=[10, 11])
system.start_api_server()

# Start processing in background thread
import threading
sources = [InputSource('video', source_path='video.mp4')]
processing_thread = threading.Thread(
    target=system.start_video_processing,
    args=(sources, False)  # No display
)
processing_thread.daemon = True
processing_thread.start()

# Use API from your application
while True:
    response = requests.get('http://localhost:8080/cars')
    cars = response.json()
    
    for car_id, car_data in cars['cars'].items():
        # Process car data in your application
        position = car_data['position_mm']
        speed = car_data['speed_mm_per_s']
        print(f"Car {car_id}: {position} at {speed}mm/s")
    
    time.sleep(0.1)  # 10 Hz updates
```

## Complete Example with Display Features

```python
from indoor_localization import LocalizationConfig, IndoorLocalizationSystem, InputSource

# Create configuration with display optimization
config = LocalizationConfig(
    map_path='city_map.png',
    car_marker_ids=[10, 11, 12],
    screen_display_height=1200,  # Optimize for your screen
    server_port=8080
)

# Create system
system = IndoorLocalizationSystem(config)
system.start_api_server()

try:
    # Process single image with display
    result = system.process_image_file('city_image_8refs.png')
    print(f"Cars detected: {len(result.car_states)}")
    
    # Real-time processing with multiple sources
    sources = [
        InputSource('video', source_path='city_video_3d.mp4'),
        InputSource('video', source_path='city_video_8refs.mp4')
    ]
    
    # Start processing with display enabled
    # Windows will automatically arrange in grid layout
    # Each window maintains aspect ratio when resized
    system.start_video_processing(sources, enable_display=True)
    
    # You can reset window sizes anytime during processing
    # system.reset_window_sizes()
    
except KeyboardInterrupt:
    print("Stopping system...")
finally:
    system.stop_api_server()
    print("System stopped")
```

## File Structure

```
indoor_localization/
├── __init__.py          # Package initialization
├── config.py            # Configuration classes
├── models.py            # Data structures
├── processor.py         # Core processing engine
├── api.py               # HTTP API server
├── localization_system.py  # Main system interface
├── numpy_json_patch.py  # NumPy JSON serialization patch
└── README.md            # This documentation
```

## Related Files

See the main project directory for:
- `main.py` - Quick start application
- `example_usage.py` - Comprehensive usage examples
- `EXAMPLE_FILES_GUIDE.md` - Guide for choosing the right file

## Requirements

### System Requirements
- Python 3.7+
- OpenCV 4.0+ (with GUI support for display features)
- NumPy 1.19+
- Standard library modules: threading, http.server, json, time, dataclasses

### Display Requirements
- **For visualization features**: OpenCV compiled with GUI support (Qt, GTK, or Win32)
- **Minimum screen resolution**: 1024x768 (recommended: 1920x1080 or higher)
- **Multiple monitor support**: Automatic window positioning across displays
- **Graphics acceleration**: Recommended for smooth rendering on high-resolution displays

### Installation Notes
```bash
# Standard installation
pip install opencv-python numpy

# For systems without display (servers)
pip install opencv-python-headless numpy
# Note: Headless version disables visualization features
```
