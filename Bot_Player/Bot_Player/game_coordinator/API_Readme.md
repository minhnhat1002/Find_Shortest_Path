# Localization API Client

This document provides an overview of the `LocalizationAPIClient`, a Python Socket.IO client for interacting with the Localization API server. It allows you to control and monitor cars in a simulated environment.

## Installation

Ensure you have the required libraries installed:

```bash
pip install -r requirements.txt
```

## Getting Started

### Creating a Client

To begin, you need to create an instance of the `LocalizationAPIClient`. You can specify the server host and port.

```python
from game_coordinator.clientApi import LocalizationAPIClient

# Create a client instance
client = LocalizationAPIClient(server_host='localhost', server_port=8080)
```

The `create_client` factory function can also be used:
```python
from game_coordinator.clientApi import create_client

client = create_client('localhost:8080')
```

### Connecting to the Server

After creating the client, you need to connect to the server using your credentials.

```python
userName = "your_username"
password = "your_password"

if client.connect(userName, password):
    print("Successfully connected to the server.")
else:
    print("Failed to connect.")
```

## API Methods

### `disconnect()`

Disconnects the client from the server.

```python
client.disconnect()
```

### `get_server_status(timeout: float = 1.0)`

Retrieves the initialization status of the server.

```python
status = client.get_server_status()
if status is not None:
    print(f"Server status: {status}")
```
**Returns**: `int` or `None`. Returns `1` if the server has finished initialization.

### `get_assign_car(timeout: float = 1.0)`

Requests the IDs of the cars assigned to your team.

```python
assigned_cars = client.get_assign_car()
if assigned_cars:
    car1_id, car2_id = assigned_cars
    print(f"Assigned cars: {car1_id}, {car2_id}")
```
**Returns**: A tuple `(car1_id, car2_id)` or `None`.

### `get_car_state(car_id: int, timeout: float = 1.0)`

Retrieves the current state of a specific car.

```python
car_id = 1 # Example car ID
car_state = client.get_car_state(car_id)
if car_state:
    print(f"Car {car_id} position: {car_state.position}")
```
**Returns**: A `CarState` object or `None`. The `CarState` object has the following attributes:
*   `id`: `int`
*   `position`: `numpy.ndarray`
*   `position_mm`: `numpy.ndarray`
*   `orientation`: `float`
*   `speed_mm_per_s`: `float`
*   `obstacles_abs`: `list` of `(distance, angle)` tuples
*   `control_command`: `str`
*   `desired_angle`: `float`
*   `route`: `list` of `(x, y)` tuples
*   `numOwnedPackages`: `int`
*   `timestamp`: `float`

### `get_road_information(timeout: float = 1.0)`

Retrieves information about the roads and points on the map.

```python
success, streets, points = client.get_road_information()
if success:
    print(f"Number of streets: {len(streets)}")
    print(f"Number of points: {len(points)}")
```
**Returns**: A tuple `(success, streets, points)` or `None`.

### `get_teams_information(timeout: float = 1.0)`

Retrieves information about all teams.

```python
success, teams_info = client.get_teams_information()
if success:
    for team in teams_info:
        print(f"Team: {team['userName']}, Score: {team['score']}")
```
**Returns**: A tuple `(success, info)` or `None`.

### `get_package_list(timeout: float = 1.0)`

Retrieves the list of available packages.

```python
success, packages = client.get_package_list()
if success:
    print(f"Available packages: {len(packages)}")
```
**Returns**: A tuple `(success, data)` where `data` is a list of packages.

### `update_car_route(car_id: int, new_route: list, userName: str = '', password: str = '', timeout: float = 1.0)`

Updates the route for a specific car.

```python
car_id = 1
new_route = [(100, 200), (300, 400)] # Example route with point IDs
if client.update_car_route(car_id, new_route, userName, password):
    print("Route updated successfully.")
```
**Returns**: `bool` indicating success or failure.

### `request_pickup_package(car_id: int, package_id: int, userName: str = '', password: str = '', timeout: float = 1.0)`

Sends a request for a car to pick up a package.

```python
car_id = 1
package_id = 101
if client.request_pickup_package(car_id, package_id, userName, password):
    print("Package pickup request sent.")
```
**Returns**: `bool` indicating success or failure.

## Real-time Event Handling

The client can handle real-time updates from the server by defining callback functions.

### `on_car_updated(data)`

This event is triggered when a car's state is updated.

```python
def handle_car_update(data):
    print(f"Car updated: {data}")

client.on_car_updated = handle_car_update
```

### `on_route_changed(data)`

This event is triggered when a car's route changes.

```python
def handle_route_change(data):
    print(f"Route changed: {data}")

client.on_route_changed = handle_route_change
```

## Full Example

```python
import time
from game_coordinator.clientApi import LocalizationAPIClient

# --- Configuration ---
SERVER_HOST = 'localhost'
SERVER_PORT = 8080
USERNAME = "your_username"
PASSWORD = "your_password"

# --- Callback functions for real-time updates ---
def on_car_updated(data):
    print(f"Received car update: {data}")

def on_route_changed(data):
    print(f"Received route change: {data}")

# --- Main Logic ---
if __name__ == "__main__":
    # 1. Create and connect the client
    client = LocalizationAPIClient(SERVER_HOST, SERVER_PORT)
    client.on_car_updated = on_car_updated
    client.on_route_changed = on_route_changed

    if not client.connect(USERNAME, PASSWORD):
        print("Connection failed. Exiting.")
        exit()

    # 2. Wait for server to initialize
    print("Waiting for server to initialize...")
    while client.get_server_status() != 1:
        time.sleep(0.1)
    print("Server is ready.")

    # 3. Get assigned cars
    cars = client.get_assign_car()
    if not cars:
        print("Could not get assigned cars. Exiting.")
        client.disconnect()
        exit()
    
    my_car_id = cars[0]
    print(f"Controlling car with ID: {my_car_id}")

    # 4. Get car state
    initial_state = client.get_car_state(my_car_id)
    if initial_state:
        print(f"Initial position of car {my_car_id}: {initial_state.position}")

    # 5. Example: Update car route
    # (Assuming you have a list of valid point IDs for the route)
    # new_route_points = [1, 5, 10] 
    # client.update_car_route(my_car_id, new_route_points, USERNAME, PASSWORD)

    # 6. Run for a while to receive real-time updates
    print("Listening for real-time updates for 30 seconds...")
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("Interrupted by user.")

    # 7. Disconnect
    print("Disconnecting...")
    client.disconnect()
    print("Done.")
```

## Disconnecting

Always remember to disconnect the client when you are done.

```python
client.disconnect()
```
