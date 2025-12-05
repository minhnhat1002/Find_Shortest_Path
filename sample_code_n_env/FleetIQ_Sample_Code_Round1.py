#!/usr/bin/env python3
"""
Sample Code for Hackathon 2025 - Elimination Round
"""
import time
from game_coordinator.clientApi import LocalizationAPIClient
import math

# Server Configuration Area #
serverHost = "localhost"  # For testing you can keep as localhost since Server will be running on your local machine
                          # During competition day, you will need to change to the provided server IP address
####################################

# Team Information Definition Area #
userName = "XinChao" # Put your team name here
password = "123456789" # Any password you want. This is to prevent other team interfering with your cars.
####################################

# Global define #
Package_List = {}
####################################

def nearest_point(car_pos, points):
    """
    Finds and returns the point from a list that is nearest to the given car position.

    Args:
        car_pos (tuple): The (x, y) coordinates of the car's position.
        points (list of tuple): A list of (x, y) coordinates representing points to compare.

    Returns:
        tuple: The (x, y) coordinates of the nearest point to the car position.
    """
    sorted_points = sorted(points, key=lambda p: math.hypot(car_pos[0] - p[0], car_pos[1] - p[1]))
    return sorted_points[0]


def calculate_optimal_route(graph, start, end):
    """
    Finds the shortest path between two nodes in a weighted graph using Dijkstra's algorithm.
    Args:
        graph (dict): A dictionary representing the graph where keys are nodes and values are lists of tuples (neighbor, weight).
        start (hashable): The starting node.
        end (hashable): The target node.
    Returns:
        list: The shortest path from start to end as a list of nodes, or None if no path exists.
    """
    import heapq
    queue = [(0, start, [start])]
    visited = set()
    while queue:
        cost, node, path = heapq.heappop(queue)
        if node == end:
            return path
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph[node]:
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
    
    return None


def calculateDistance(currentPos, Destination):
    """
    Calculates the Euclidean distance between the current position and the destination.

    Args:
        currentPos (tuple): A tuple (x, y) representing the current position.
        Destination (tuple): A tuple (x, y) representing the destination position.

    Returns:
        float: The Euclidean distance between currentPos and Destination.
    """
    car_x, car_y = currentPos
    dest_x, dest_y = Destination
    dx = dest_x - car_x
    dy = dest_y - car_y
    distance = math.hypot(dx, dy)
    return distance


def find_nearest_package(car_pos, package_list, current_own_packages):
    """
    Finds the nearest available package to the car's current position.

    Args:
        car_pos (tuple): The (x, y) coordinates of the car's current position.
        package_list (dict): A dictionary of package information, where each key is a package ID and each value is a dict containing package details, including "status" and "position_end".
        current_own_packages (set or list): A collection of package IDs that are currently owned and should be excluded from consideration.

    Returns:
        tuple: A tuple containing the ID of the nearest package (or None if no package is found) and the distance to that package.
    """
    nearest_package_id = None
    nearest_distance = float('inf')
    for package_id, package in package_list.items():
        if package["status"] == 0 and package_id not in current_own_packages:
            # Use the first position_end for distance calculation
            pos = package["position_end"]
            distance = math.hypot(car_pos[0] - pos[0], car_pos[1] - pos[1])
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_package_id = package_id
    return nearest_package_id, nearest_distance


def main():
    """Main function to simulate a client connecting to the API server"""
    print("=== Localization API Client Simulation ===")
    
    # Create a client instance
    client = LocalizationAPIClient(server_host=serverHost, server_port=8080)
    
    # Try to connect to the server
    print("Attempting to connect to the localization server...")
    if not client.connect(userName, password):
        print("Failed to connect to the server. Make sure the server is running.")
        print("You can start the server by running the localization system.")
        return

    print("✓ Successfully connected to the server!")

    # Loop until Server finish initialization
    status = client.get_server_status()
    while not status:
        time.sleep(0.1) # Get Server status every 100ms
        status = client.get_server_status()

    # Get assign car
    Car_1_ID, Car_2_ID = client.get_assign_car()

    # Continuous monitoring loop
    print(f"\n=== Starting Continuous Monitoring for Car {Car_1_ID} and Car {Car_2_ID}===")
    print("Press Ctrl+C to stop monitoring...")
    
    # LOCAL VARIABLES
    loop_count = 0 # Number of execution loop

    getPackageData = False # Status of getting package data

    # Initial variable for Car 1 and Car 2 since we can control up to 2 cars at the same time
    car_1_nearest_Package = [99] # Intial nearest package ID
    car_2_nearest_Package = [99] # Intial nearest package ID
    
    car_1_Request_Pickup_Package_Flg = True # Flag to indicate request pick up package
    car_2_Request_Pickup_Package_Flg = True # Flag to indicate request pick up package

    car_1_Request_Calculate_Route_Flg = False # Flag to indicate request calculate route
    car_2_Request_Calculate_Route_Flg = False # Flag to indicate request calculate

    car_1_target_destination = [] # Initial target destination
    car_2_target_destination = [] # Initial target destination

    car_1_num_owned_package = 0 # Number of car 1 owned package
    car_2_num_owned_package = 0 # Number of car 2 owned package
    ####################################

    print("Try to get map data")
    # Server already handle GeoJSON data internally, so just get streets and points
    # or you can try to improve speed by using directly GeoJSON data provided locally to you
    time.sleep(0.1)
    success, streets, points = client.get_road_information()

    if success:
        print("✓ Get MAP information successful!")
    else:
        print("X Get MAP information failed")
    
    try:
        while True:
            loop_count += 1
            print(f"\n--- Loop {loop_count} at {time.strftime('%H:%M:%S')} ---")
            
            # Try to get Car State
            try:
                # Check if still connected before making request
                if not client.is_connected:
                    print("⚠ Client disconnected, attempting to reconnect...")
                    if not client.connect():
                        print("✗ Failed to reconnect")
                        continue
                # Request to get Car State information, timeout = 5 seconds
                time.sleep(0.1)
                car_1_state = client.get_car_state(Car_1_ID, timeout=5)
                time.sleep(0.1)
                car_2_state = client.get_car_state(Car_2_ID, timeout=5)

                # Print out Car information for debugging
                try:
                    print(f"---- CAR {Car_1_ID} INFORMATION ----")
                    print(f"Position in mm                      : {car_1_state.position_mm}")
                    print(f"Command                             : {car_1_state.control_command}")
                    print(f"Number of owned packages            : {car_1_state.numOwnedPackages}")
                except:
                    time.sleep(1)
                    continue
                try:
                    print(f"---- CAR {Car_2_ID} INFORMATION ----")
                    print(f"Position in mm                      : {car_2_state.position_mm}")
                    print(f"Command                             : {car_2_state.control_command}")
                    print(f"Number of owned packages            : {car_2_state.numOwnedPackages}")
                except:
                    time.sleep(1)
                    continue

                # Only if already get package data, start to process package handling
                if getPackageData:
                    # If Car is in PICK UP state
                    # and near enough to Hub: 
                    # first calculate which package to pick up
                    # then request to pick up package

                    #### THIS IS WHERE YOU IMPLEMENT YOUR PACKAGE CHOSING ALGORITHM ####
                    if car_1_Request_Pickup_Package_Flg:
                        # Check whether Car is close enough to Hub
                        # Calculate Distance from Car to Warehouse
                        dest_x, dest_y = Package_List['1']["position_start"][0] # Each package can be pick up at 4 position around Hub, here we only consider first position
                        if car_1_state is not None:
                            distance = calculateDistance(car_1_state.position, (dest_x, dest_y))
                            if distance <= 36: # Tolerance distance 36mm
                                if car_1_num_owned_package == 0:
                                    package_id, distance = find_nearest_package(car_1_state.position, Package_List, car_1_nearest_Package)
                                    time.sleep(0.1)
                                    if client.request_pickup_package(Car_1_ID, package_id, userName, password):
                                        car_1_nearest_Package = [package_id]
                                        car_1_target_destination = [Package_List[package_id]["position_end"]]
                                        car_1_num_owned_package += 1
                                    else:
                                        print("Pick up fail")
                                if car_1_num_owned_package == 1:
                                    package_id, distance = find_nearest_package(car_1_state.position, Package_List, car_1_nearest_Package)
                                    time.sleep(0.1)
                                    if client.request_pickup_package(Car_1_ID, package_id, userName, password):
                                        car_1_nearest_Package.append(package_id)
                                        car_1_target_destination.append(Package_List[package_id]["position_end"])
                                        car_1_num_owned_package += 1
                                    else:
                                        print("Pick up fail")
                                if car_1_num_owned_package == 2:
                                    package_id, distance = find_nearest_package(car_1_state.position, Package_List, car_1_nearest_Package)
                                    time.sleep(0.1)
                                    if client.request_pickup_package(Car_1_ID, package_id, userName, password):
                                        car_1_nearest_Package.append(package_id)
                                        car_1_target_destination.append(Package_List[package_id]["position_end"])
                                        car_1_num_owned_package += 1
                                        car_1_Request_Pickup_Package_Flg = False # Get enough package
                                    else:
                                        print("Pick up fail")
                            else: # Still too far from Hub. Request Car to go to Pick up position
                                print("Car is far from Hub, requesting to go to Hub first")
                                car_1_target_destination = [[dest_x, dest_y]]
                                car_1_Request_Calculate_Route_Flg = True # Request to calculate route to Hub

                            # Double check from Server to see whether we actually get all 3 packages successfully or not
                            if car_1_num_owned_package == 3 or car_1_state.numOwnedPackages == 3:
                                print("Verifying pick up status from Server...")
                                time.sleep(0.1)
                                car_1_state = client.get_car_state(Car_1_ID, timeout=5)
                                if car_1_state.numOwnedPackages == car_1_num_owned_package:
                                    print(f"✓ Car {Car_1_ID} successfully picked up {car_1_num_owned_package} packages")
                                    car_1_Request_Calculate_Route_Flg = True # Request to calculate route to Hub
                                else:
                                    print(f"✗ Car {Car_1_ID} pick up package failed, retrying...")
                                    car_1_num_owned_package = car_1_state.numOwnedPackages # Get data from Server again
                                    car_1_Request_Pickup_Package_Flg = False # Request to pick up package again
                    ### END OF PACKAGE CHOOSING ALGORITHM ###

                    ### THIS IS WHERE WE SWITCHING BETWEEN PICKUP STATE AND DELIVERY STATE ###
                    # MONITOR UNTIL OUR PACKAGE STATUS MARKED AS DELIVERED
                    if car_1_state.numOwnedPackages == (car_1_num_owned_package - 1):
                        print(f"✓ Car {Car_1_ID} successfully delivered a package")
                        car_1_num_owned_package -= 1 
                        car_1_target_destination.pop(0) # Remove the first index of car_1_target_destination
                        car_1_Request_Calculate_Route_Flg = True
                        if len(car_1_target_destination) == 0:
                            car_1_target_destination = [] # Initial target destination
                            car_1_Request_Pickup_Package_Flg = True # Request to pick up package again
                            car_1_Request_Calculate_Route_Flg = False # Stop calculating route
                            car_1_nearest_Package = [99] # Reset nearest package ID
                    ### END OF SWITCHING BETWEEN PICKUP STATE AND DELIVERY STATE ###

                    # Now already get 3 package, start to calcualte way to deliver
                    # Deliver sequence : most nearest, second nearest, and then third nearest

                    ### THIS IS WHERE YOU IMPLEMENT YOUR PACKAGE DELIVERY ALGORITHM ###
                    if car_1_Request_Calculate_Route_Flg:
                        valid_points = [tuple(p) for p in points]
                        valid_streets = streets
                        graph = {p: [] for p in valid_points}
                        
                        for street in streets:
                            # Convert street coordinates to tuples
                            start_pt = tuple(street["start"])
                            end_pt = tuple(street["end"])
                            
                            if start_pt in valid_points and end_pt in valid_points:
                                length = math.hypot(end_pt[0] - start_pt[0], end_pt[1] - start_pt[1])
                                graph[start_pt].append((end_pt, length))
                                graph[end_pt].append((start_pt, length))

                        car_pos = (car_1_state.position_mm[0], car_1_state.position_mm[1]) # Current Car Position
                        end_node = nearest_point(car_1_target_destination[0], valid_points) # Always go to 1st Destination
                        start_node = nearest_point(car_pos, valid_points) # Start Node is nearest node to Car
                        route_car_1 = calculate_optimal_route(graph, start_node, end_node) # Use Dijkstra to calculate shortest path

                        if route_car_1 is not None:
                            # Handle case when destination is shorter than end node
                            pathLen = len(route_car_1)
                            lastNode = route_car_1[pathLen - 1]
                            if calculateDistance(route_car_1[pathLen - 2], car_1_target_destination[0]) > calculateDistance(route_car_1[pathLen - 2], lastNode):
                                route_car_1.append(car_1_target_destination[0])
                            else:
                                route_car_1[pathLen - 1] = car_1_target_destination[0]
                            # Handle case when destination is in the same street, but start node is further than current position
                            startNode = route_car_1[0]
                            if calculateDistance(startNode, route_car_1[1]) > calculateDistance(car_1_state.position, route_car_1[1]):
                                route_car_1[0] = (car_1_state.position[0],car_1_state.position[1])
                        else:
                            route_car_1 = car_1_target_destination[0]
                                
                        if route_car_1:
                            print(f"Route calculated with {len(route_car_1)} waypoints")
                        else:
                            print("No route found!")
                            route_car_1 = []  # Initialize empty route if no path found
                        # Submit route to Server
                        time.sleep(0.1)
                        success = client.update_car_route(Car_1_ID, route_car_1, userName, password, timeout=5.0)
                        if success:
                            print("✓ Route update successful!")
                            # Get updated car state to verify route was set
                            time.sleep(0.5)  # Give server time to process
                            updated_state = client.get_car_state(Car_1_ID, timeout=5.0)
                            if updated_state and updated_state.route:
                                print(f"✓ Verified: Car now has {len(updated_state.route)} route points")
                                print("New route points:")
                                for i, (x, y) in enumerate(updated_state.route):
                                    print(f"  {i+1}: ({x}, {y})")
                                car_1_Request_Calculate_Route_Flg = False # Only calcualte one time, reset only when finish delivery current package
                            else:
                                print("⚠ Warning: Could not verify route update")
                        else:
                            print("✗ Route update failed!")
                    ### END OF PACKAGE DELIVERY ALGORITHM ###
            
            except Exception as e:
                print(f"✗ Error while getting car state: {e}")

            if loop_count % 2 == 0: # Get package list every 2 loops
                time.sleep(0.1)
                success, Package_List = client.get_package_list()
                # Calculate Distance from current Truck position to all packages

                # Print out package information to debug purpose
                # Be careful when printing too much information may slow down the loop
                # We have total 80 packages
                '''print("PACKAGE INFORMATION")
                for package_id, package in Package_List.items():
                    print(f"Package ID : {package_id}")
                    print(f"Position Start : {package['position_start']}")
                    print(f"Position End : {package['position_end']}")
                    print(f"Ownwed by : {package['ownedBy']}")
                    print(f"Status : {package['status']}")'''
                # Only after get package information sucessfully, we will start to choose which package to pick up
                if success:
                    print("✓ Get Package List information successful!")
                    getPackageData = True
                else:
                    print("X Get Package List information failed!")
                    getPackageData = False
                                     
            if loop_count % 3 == 0: # Get team information every 3 loops
                time.sleep(0.1)
                success, team_info = client.get_teams_information()
                print("\n=== Team Information ===")
                if success:
                    for teamName in team_info:
                        info = team_info[teamName]
                        print(f"Team Name: {teamName}")
                        print(f"Score: {info['point']}")
                        print(f"Travel Distance: {info['travel_distance']}")

            print(f"\nSleeping for 1 seconds...")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n=== Monitoring stopped by user after {loop_count} loops ===")
    except Exception as e:
        print(f"\n✗ Unexpected error in monitoring loop: {e}")
    
    # Set up real-time callbacks for demonstration
    
    # Disconnect
    client.disconnect()
    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    # Check command line arguments
    main()