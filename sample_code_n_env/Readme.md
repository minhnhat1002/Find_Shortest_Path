# Explanation for `FleetIQ_Sample_Code_Round1.py`

This document provides a detailed explanation of the `FleetIQ_Sample_Code_Round1.py` script, which is a sample for the Hackathon 2025 Elimination Round. The script acts as a client to interact with a localization API server, controlling autonomous cars to pick up and deliver packages.

## 1. Overview

The script connects to a server that simulates a warehouse environment with autonomous cars. The main objective is to program these cars to efficiently collect packages from a central hub and deliver them to specified destinations. This sample code provides the basic structure for server communication, car control, and a simple logic for package management and delivery.

## 2. Configuration

Before running the script, you need to set up the following configuration variables at the top of the file.

### Server Configuration

```python
# Server Configuration Area #
serverHost = "localhost"  # For testing you can keep as localhost since Server will be running on your local machine
                          # During competition day, you will need to change to the provided server IP address
####################################
```

-   `serverHost`: This is the IP address of the localization server. For local development and testing, it's set to `localhost`. During the competition, you will need to change this to the IP address provided by the organizers.

### Team Information

```python
# Team Information Definition Area #
userName = "Team_BTC" # Put your team name here
password = "123456789" # Any password you want. This is to prevent other team interfering with your cars.
####################################
```

-   `userName`: Your unique team name.
-   `password`: A password to ensure that only your team can control your cars.

## 3. Key Functions

The script includes several helper functions for common calculations.

### `nearest_point(car_pos, points)`

-   **Purpose**: To find the closest map node (point) to the car's current position. This is useful for aligning the car's location with the nearest valid point on the road network before calculating a route.
-   **Arguments**:
    -   `car_pos`: A tuple `(x, y)` representing the car's current coordinates.
    -   `points`: A list of valid points (nodes) on the map.
-   **Returns**: The coordinates of the nearest point.

### `calculate_optimal_route(graph, start, end)`

-   **Purpose**: Implements Dijkstra's algorithm to find the shortest path between two nodes in the graph that represents the road network.
-   **Arguments**:
    -   `graph`: A dictionary representing the road network, where keys are nodes (points) and values are lists of tuples `(neighbor_node, weight)`, with `weight` being the distance.
    -   `start`: The starting node for the path.
    -   `end`: The destination node.
-   **Returns**: A list of nodes that form the shortest path, or `None` if no path is found.

### `calculateDistance(currentPos, Destination)`

-   **Purpose**: Calculates the straight-line (Euclidean) distance between two points.
-   **Arguments**:
    -   `currentPos`: A tuple `(x, y)` for the starting position.
    -   `Destination`: A tuple `(x, y)` for the end position.
-   **Returns**: The distance as a float.

### `find_nearest_package(car_pos, package_list, current_own_packages)`

-   **Purpose**: Finds the nearest available package to the car's current position.
-   **Arguments**:
    -   `car_pos`: The car's current coordinates.
    -   `package_list`: A dictionary containing information about all packages.
    -   `current_own_packages`: A list of package IDs that the car already owns, to exclude them from the search.
-   **Returns**: A tuple containing the ID of the nearest package and the distance to it.

## 4. Main Logic (`main` function)

The `main` function contains the primary logic of the client.

### Connection and Initialization

1.  **Connect to Server**: It starts by creating a `LocalizationAPIClient` instance and connecting to the server using the configured host, team name, and password.
2.  **Wait for Server**: It waits until the server is fully initialized.
3.  **Get Assigned Cars**: It retrieves the IDs of the two cars assigned to the team (`Car_1_ID`, `Car_2_ID`).
4.  **Get Map Data**: It fetches the road network information (streets and points) from the server.

### Main Monitoring Loop

The script then enters an infinite loop to continuously monitor and control the cars.

-   **Get Car State**: In each loop, it requests the current state of both cars, which includes their position, current command, and the number of packages they own.
-   **Package Pickup Logic**:
    -   This section is marked with `#### THIS IS WHERE YOU IMPLEMENT YOUR PACKAGE CHOSING ALGORITHM ####`.
    -   The sample logic checks if a car is near the pickup hub.
    -   If it is, it uses `find_nearest_package` to select up to three packages and requests to pick them up one by one.
    -   If the car is far from the hub, it sets a route to the hub first.
-   **Package Delivery Logic**:
    -   This section is marked with `#### THIS IS WHERE YOU IMPLEMENT YOUR PACKAGE DELIVERY ALGORITHM ####`.
    -   After picking up packages, the car needs to deliver them.
    -   The sample logic takes the first destination from its target list.
    -   It uses `calculate_optimal_route` to find the shortest path from the car's current position to the destination.
    -   The calculated route is then sent to the server for the car to follow.
-   **State Switching**:
    -   The script monitors the number of owned packages. When a package is delivered, the count decreases.
    -   The script then removes the delivered package's destination from its target list and calculates the route to the next destination.
    -   Once all packages are delivered, it switches back to pickup mode.
-   **Data Refresh**:
    -   Periodically, the script fetches the updated list of all packages and the current scores of all teams.

### How to Run the Script

To run the script, you need to have Python 3 installed. You can execute it from your terminal:

```bash
python FleetIQ_Sample_Code_Round1.py
```

Make sure the server application is running before you start the client.

### Areas for Customization

The key to success in the hackathon is to implement more sophisticated algorithms in the following areas:

1.  **Package Choosing Algorithm**: The current implementation picks the nearest available packages. A better strategy might consider the package destinations to group packages that are delivered to nearby locations.
2.  **Package Delivery Algorithm**: The sample code delivers packages in the order they were picked up. Optimizing the delivery route (e.g., solving a Traveling Salesperson Problem for the current set of packages) can significantly improve efficiency.
3.  **Multi-Car Coordination**: The sample code controls `Car_1` and has placeholder logic for `Car_2`. A good solution will require coordinating both cars to work together, for example, by dividing the packages or delivery zones between them.

This explanation should help you understand the sample code and provide a solid foundation for developing your own advanced solution for the hackathon. Good luck!
