#!/usr/bin/env python3
"""
FleetIQ V4 Strategy - Standalone
Strictly follows FleetIQ_Sample_Code_Round1.py structure and API signatures,
with V4 enhancements: profit-based selection + TSP-optimized delivery order.
"""
import time
import math
import heapq
import itertools
from game_coordinator.clientApi import LocalizationAPIClient

# Server Configuration Area #
serverHost = "localhost"
####################################

# Team Information Definition Area #
userName = "Team_KeoDeoKimYen2"
password = "123456789"
####################################

# Global define #
Package_List = {}
GLOBAL_GRAPH = None
GLOBAL_VALID_POINTS = None
SCORE_CACHE = {}
RESERVED_PACKAGES = {}  # {package_id: car_id} - shared reservation between cars
####################################


def build_graph_once(streets, points):
    """Build road graph once and cache it globally."""
    valid_points = [tuple(p) for p in points]
    graph = {p: [] for p in valid_points}
    for street in streets:
        start_pt = tuple(street["start"])
        end_pt = tuple(street["end"])
        if start_pt in valid_points and end_pt in valid_points:
            length = math.hypot(end_pt[0] - start_pt[0], end_pt[1] - start_pt[1])
            graph[start_pt].append((end_pt, length))
            graph[end_pt].append((start_pt, length))
    return graph, valid_points


def nearest_point(car_pos, points):
    """
    Finds and returns the point from a list that is nearest to the given car position.
    Args:
        car_pos (tuple): (x, y)
        points (list[tuple]): list of (x, y)
    Returns:
        tuple: nearest (x, y)
    """
    sorted_points = sorted(points, key=lambda p: math.hypot(car_pos[0] - p[0], car_pos[1] - p[1]))
    return sorted_points[0]

def calculateDistance(a, b):
    """Sample-compatible distance function using Euclidean norm.
    Accepts tuples/lists (x, y)."""
    try:
        ax, ay = a[0], a[1]
        bx, by = b[0], b[1]
    except Exception:
        # Fallback in case of unexpected inputs
        return float('inf')
    return math.hypot(ax - bx, ay - by)


def calculate_optimal_route(graph, start, end):
    """Dijkstra shortest path from start to end over graph."""
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
    
def profit_score(car_pos, hub_pos, dest_pos, graph=None, points=None):
    """
    Scoring aligned with rules:
    - All packages have equal value; objective is to minimize fuel (distance) per delivery.
    - Prefer packages that add minimal route distance: car->hub entrance + hub->destination.
    Uses pre-built graph when available; otherwise falls back to Euclidean.
    Returns a higher score for lower cost by inverting the cost.
    """
    # Check cache first (round to 10mm for cache key)
    cache_key = (round(car_pos[0]/10)*10, round(car_pos[1]/10)*10, 
                 round(hub_pos[0]/10)*10, round(hub_pos[1]/10)*10,
                 round(dest_pos[0]/10)*10, round(dest_pos[1]/10)*10)
    if cache_key in SCORE_CACHE:
        return SCORE_CACHE[cache_key]
    
    def graph_distance(a, b):
        if graph is None or points is None:
            return calculateDistance(a, b)
        s = nearest_point(a, points)
        e = nearest_point(b, points)
        path = calculate_optimal_route(graph, s, e)
        if not path or len(path) < 2:
            return calculateDistance(a, b)
        return sum(calculateDistance(path[i], path[i+1]) for i in range(len(path)-1))

    pickup_cost = graph_distance(car_pos, hub_pos)
    delivery_cost = graph_distance(hub_pos, dest_pos)
    total_cost = pickup_cost + delivery_cost
    score = 1.0 / (total_cost + 1e-6)
    
    # Cache the result
    SCORE_CACHE[cache_key] = score
    return score

def nearest_hub_entrance(car_pos, package):
    """
    Select the nearest pickup entrance from position_start for the given package.
    position_start is typically a list of entrances around the hub.
    """
    entrances = package.get("position_start", [])
    if not entrances:
        return None
    cpos = (car_pos[0], car_pos[1])
    return min(entrances, key=lambda e: calculateDistance(cpos, (e[0], e[1])) if 'calculateDistance' in globals() else math.hypot(cpos[0]-e[0], cpos[1]-e[1]))

def find_best_packages_v4(car_pos, package_list, current_own_packages, hub_pos, max_packages=3, graph=None, points=None, car_id=None):
    """
    Select top packages by profit score, excluding already owned and reserved by other cars.
    Returns [(package_id, dest_pos)] sorted by score desc.
    """
    scored = []
    filtered_count = {"total": 0, "status_not_0": 0, "already_owned": 0, "reserved": 0}
    
    for package_id, package in package_list.items():
        filtered_count["total"] += 1
        # Skip if package is unavailable, already owned, or reserved by another car
        if package.get("status") != 0:
            filtered_count["status_not_0"] += 1
            continue
        if package_id in current_own_packages:
            filtered_count["already_owned"] += 1
            continue
        # Check if reserved by another car
        if package_id in RESERVED_PACKAGES and RESERVED_PACKAGES[package_id] != car_id:
            filtered_count["reserved"] += 1
            continue
        
        dest_pos = package["position_end"]
        entrance = nearest_hub_entrance(car_pos, package)
        hub_eff = hub_pos if entrance is None else (entrance[0], entrance[1])
        # All packages equal value; minimize added route distance
        score = profit_score(car_pos, hub_eff, dest_pos, graph=graph, points=points)
        scored.append((package_id, dest_pos, score))
    
    if len(scored) == 0 and filtered_count["total"] > 0:
        print(f"   ⚠ Filtered all {filtered_count['total']} packages: status≠0={filtered_count['status_not_0']}, owned={filtered_count['already_owned']}, reserved={filtered_count['reserved']}")
    
    scored.sort(key=lambda t: t[2], reverse=True)
    return [(pid, dest) for pid, dest, _ in scored[:max_packages]]


def tsp_order(start_pos, destinations, graph, points):
    """
    Compute TSP order for destinations using route distance over pre-built graph.
    Returns a list of indices indicating visit order.
    """
    if not destinations:
        return []
    if len(destinations) == 1:
        return [0]

    def route_distance(a, b):
        s = nearest_point(a, points)
        e = nearest_point(b, points)
        path = calculate_optimal_route(graph, s, e)
        if not path or len(path) < 2:
            return float('inf')
        return sum(calculateDistance(path[i], path[i+1]) for i in range(len(path)-1))

    min_dist = float('inf')
    best_perm = list(range(len(destinations)))
    for perm in itertools.permutations(range(len(destinations))):
        dist = 0.0
        cur = start_pos
        ok = True
        for idx in perm:
            dpos = destinations[idx]
            rd = route_distance(cur, dpos)
            if rd == float('inf'):
                ok = False
                break
            dist += rd
            cur = dpos
        if ok and dist < min_dist:
            min_dist = dist
            best_perm = list(perm)
    return best_perm


def attempt_pickup_with_retry(client, car_id, package_candidates, user, pwd, max_attempts=3):
    """
    Try to pickup packages with fallback to next-best.
    Returns (package_id, dest) on success, None on failure.
    Updates RESERVED_PACKAGES on success.
    """
    attempts = 0
    for package_id, dest in package_candidates:
        if attempts >= max_attempts:
            break
        attempts += 1
        # Reserve package before attempting pickup
        RESERVED_PACKAGES[package_id] = car_id
        time.sleep(0.06)
        if client.request_pickup_package(car_id, package_id, user, pwd):
            return (package_id, dest)
        else:
            print(f"⚠ Attempt {attempts}: Package {package_id} unavailable, trying next...")
            # Remove reservation if pickup failed
            if package_id in RESERVED_PACKAGES and RESERVED_PACKAGES[package_id] == car_id:
                del RESERVED_PACKAGES[package_id]
    return None


def rolling_capacity_pickup(client, car_id, car_pos, hub_pos, owned_ids, target_dest_list, num_owned, max_capacity, user, pwd):
    """
    Phase 2: Rolling capacity - top up to max_capacity at hub.
    Returns (updated_owned_ids, updated_target_destinations, updated_num_owned)
    """
    print(f"🔄 Rolling capacity pickup for {car_id}: current={num_owned}, target={max_capacity}")
    print(f"   DEBUG: Package_List has {len(Package_List)} packages")
    print(f"   DEBUG: Currently owned IDs: {owned_ids}")
    print(f"   DEBUG: Reserved packages: {RESERVED_PACKAGES}")
    
    while num_owned < max_capacity:
        best = find_best_packages_v4(car_pos, Package_List, owned_ids, hub_pos, 
                                     max_packages=(max_capacity - num_owned), 
                                     graph=GLOBAL_GRAPH, points=GLOBAL_VALID_POINTS, 
                                     car_id=car_id)
        print(f"   DEBUG: find_best_packages_v4 returned {len(best) if best else 0} candidates")
        if not best:
            print(f"No more packages available for {car_id}")
            print(f"   Reason: Package_List empty={len(Package_List)==0}, or all filtered out")
            break
        result = attempt_pickup_with_retry(client, car_id, best, user, pwd, max_attempts=2)
        if result:
            package_id, dest = result
            owned_ids.append(package_id)
            target_dest_list.append(dest)
            num_owned += 1
            print(f"✓ {car_id} picked up package {package_id} ({num_owned}/{max_capacity})")
        else:
            print(f"⚠ {car_id} failed to pickup any packages from candidates")
            break
    return owned_ids, target_dest_list, num_owned


def main():
    print("=== FleetIQ V4 Standalone ===")
    client = LocalizationAPIClient(server_host=serverHost, server_port=8080)
    print("Connecting...")
    if not client.connect(userName, password):
        print("Failed to connect")
        return
    print("✓ Connected")
    status = client.get_server_status()
    while not status:
        time.sleep(0.06)
        status = client.get_server_status()

    Car_1_ID, Car_2_ID = client.get_assign_car()
    print(f"Cars assigned: {Car_1_ID}, {Car_2_ID}")

    # Local variables
    loop_count = 0
    getPackageData = False

    car_1_Request_Pickup_Package_Flg = True
    car_1_Request_Calculate_Route_Flg = False
    car_1_target_destination = []
    car_1_num_owned_package = 0
    car_1_owned_ids = []
    # Use an ordered delivery queue instead of index list to prevent index shift issues
    car_1_delivery_queue = []

    # Car 2 variables
    car_2_Request_Pickup_Package_Flg = True
    car_2_Request_Calculate_Route_Flg = False
    car_2_target_destination = []
    car_2_num_owned_package = 0
    car_2_owned_ids = []
    car_2_delivery_queue = []

    print("Try to get map data")
    time.sleep(0.06)
    success, streets, points = client.get_road_information()
    if success:
        print("✓ Get MAP information successful!")
    else:
        print("X Get MAP information failed")
        return
    
    # Phase 1 Enhancement: Pre-build graph once
    global GLOBAL_GRAPH, GLOBAL_VALID_POINTS
    print("Building road graph (one-time setup)...")
    GLOBAL_GRAPH, GLOBAL_VALID_POINTS = build_graph_once(streets, points)
    print(f"✓ Graph built: {len(GLOBAL_VALID_POINTS)} nodes, ready for fast routing")

    try:
        while True:
            loop_count += 1
            print(f"\n--- Loop {loop_count} at {time.strftime('%H:%M:%S')} ---")
            
            # Refresh package list FIRST (every 2 loops) so pickup logic has fresh data
            if loop_count % 2 == 0:
                time.sleep(0.06)
                global Package_List  # CRITICAL: Update the global variable, not create a local one!
                success, Package_List = client.get_package_list()
                if success:
                    print(f"✓ Get Package List information successful! ({len(Package_List)} packages)")
                    if len(Package_List) > 0:
                        # Show first package as example
                        sample_id = next(iter(Package_List))
                        sample_pkg = Package_List[sample_id]
                        print(f"   Example package {sample_id}: status={sample_pkg.get('status')}, start={sample_pkg.get('position_start', [])[:1]}")
                    getPackageData = True
                else:
                    print("X Get Package List information failed!")
                    getPackageData = False
            
            # Car states
            time.sleep(0.06)
            car_1_state = client.get_car_state(Car_1_ID, timeout=5)
            time.sleep(0.06)
            car_2_state = client.get_car_state(Car_2_ID, timeout=5)
            try:
                print(f"---- CAR {Car_1_ID} INFORMATION ----")
                print(f"Position in mm                      : {car_1_state.position_mm}")
                print(f"Command                             : {car_1_state.control_command}")
                print(f"Number of owned packages            : {car_1_state.numOwnedPackages}")
                print(f"---- CAR {Car_2_ID} INFORMATION ----")
                print(f"Position in mm                      : {car_2_state.position_mm}")
                print(f"Command                             : {car_2_state.control_command}")
                print(f"Number of owned packages            : {car_2_state.numOwnedPackages}")
            except:
                time.sleep(1)
                continue

            if getPackageData:
                if car_1_Request_Pickup_Package_Flg:
                    # Hub position from any package's position_start[0]
                    try:
                        # Choose nearest entrance to current car position using any available package
                        any_pkg = next(iter(Package_List.values()))
                        nearest_entrance = nearest_hub_entrance((car_1_state.position[0], car_1_state.position[1]), any_pkg)
                        if nearest_entrance is not None:
                            dest_x, dest_y = nearest_entrance[0], nearest_entrance[1]
                        else:
                            dest_x, dest_y = any_pkg["position_start"][0]
                    except Exception:
                        # Fallback: pick first entrance of first package
                        any_pkg = next(iter(Package_List.values()))
                        dest_x, dest_y = any_pkg["position_start"][0]
                    # Distance to hub
                    distance = calculateDistance(car_1_state.position, (dest_x, dest_y))
                    if distance <= 36:
                        car_pos = (car_1_state.position[0], car_1_state.position[1])
                        hub_pos = (dest_x, dest_y)
                        # Clear any navigation-only destinations before pickup
                        car_1_target_destination = []
                        car_1_delivery_queue = []
                        # Phase 2: Rolling capacity pickup - top up to 3 packages
                        initial_owned = car_1_num_owned_package
                        car_1_owned_ids, car_1_target_destination, car_1_num_owned_package = rolling_capacity_pickup(
                            client, Car_1_ID, car_pos, hub_pos, 
                            car_1_owned_ids, car_1_target_destination, car_1_num_owned_package,
                            max_capacity=3, user=userName, pwd=password
                        )
                        
                        # If we picked up to capacity, disable pickup flag
                        if car_1_num_owned_package >= 3:
                            car_1_Request_Pickup_Package_Flg = False
                        
                        # If we picked up any new packages, recompute TSP
                        if car_1_num_owned_package > initial_owned and car_1_num_owned_package > 0:
                            print("Recomputing TSP after rolling capacity pickup...")
                            tsp_idx_order = tsp_order(car_pos, car_1_target_destination, GLOBAL_GRAPH, GLOBAL_VALID_POINTS)
                            car_1_delivery_queue = [car_1_target_destination[i] for i in tsp_idx_order]
                            print(f"Updated TSP queue: {car_1_delivery_queue}")
                            car_1_Request_Calculate_Route_Flg = True
                    else:
                        print("Car is far from Hub, requesting to go to Hub first")
                        car_1_target_destination = [(dest_x, dest_y)]
                        car_1_Request_Calculate_Route_Flg = True

                    # Note: Pickup verification and TSP computation now handled within rolling_capacity_pickup
                    # No separate verification needed since rolling capacity does pickup + TSP in one step

                # Delivery monitoring
                if car_1_state.numOwnedPackages == (car_1_num_owned_package - 1):
                    print(f"✓ Car {Car_1_ID} successfully delivered a package")
                    car_1_num_owned_package -= 1
                    # Remove the first destination in the ordered delivery queue (safe pop)
                    if car_1_delivery_queue:
                        delivered_dest = car_1_delivery_queue.pop(0)
                        # Also remove from the original list if present (keeps both in sync)
                        try:
                            car_1_target_destination.remove(delivered_dest)
                        except ValueError:
                            pass
                    else:
                        # Fallback to sequential behavior
                        if car_1_target_destination:
                            car_1_target_destination.pop(0)
                    
                    # Phase 2: Opportunistic refill - only if no more deliveries pending
                    if car_1_num_owned_package < 3 and len(car_1_target_destination) == 0:
                        try:
                            any_pkg = next(iter(Package_List.values()))
                            nearest_entrance = nearest_hub_entrance(
                                (car_1_state.position[0], car_1_state.position[1]), any_pkg)
                            if nearest_entrance:
                                hub_dist = calculateDistance(car_1_state.position, nearest_entrance)
                                if hub_dist <= 36:
                                    print(f"🔄 Opportunistic refill: Car 1 near hub after delivery (dist={hub_dist:.1f}mm)")
                                    car_pos = (car_1_state.position[0], car_1_state.position[1])
                                    hub_pos = (nearest_entrance[0], nearest_entrance[1])
                                    initial_owned = car_1_num_owned_package
                                    car_1_owned_ids, car_1_target_destination, car_1_num_owned_package = rolling_capacity_pickup(
                                        client, Car_1_ID, car_pos, hub_pos,
                                        car_1_owned_ids, car_1_target_destination, car_1_num_owned_package,
                                        max_capacity=3, user=userName, pwd=password
                                    )
                                    # Recompute TSP with new packages
                                    if car_1_num_owned_package > initial_owned:
                                        tsp_idx_order = tsp_order(car_pos, car_1_target_destination, GLOBAL_GRAPH, GLOBAL_VALID_POINTS)
                                        car_1_delivery_queue = [car_1_target_destination[i] for i in tsp_idx_order]
                                        print(f"Updated TSP queue after refill: {car_1_delivery_queue}")
                        except StopIteration:
                            pass
                    
                    # Always set route flag if there are still destinations pending
                    if len(car_1_target_destination) > 0:
                        car_1_Request_Calculate_Route_Flg = True
                    if len(car_1_target_destination) == 0:
                        car_1_target_destination = []
                        car_1_Request_Pickup_Package_Flg = True
                        car_1_Request_Calculate_Route_Flg = False
                        car_1_owned_ids = []

                # Delivery routing (using pre-built graph)
                if car_1_Request_Calculate_Route_Flg and len(car_1_target_destination) > 0:
                    car_pos_mm = (car_1_state.position_mm[0], car_1_state.position_mm[1])
                    # Choose next destination from ordered delivery queue if available
                    if car_1_delivery_queue:
                        target_dest = car_1_delivery_queue[0]
                    else:
                        target_dest = car_1_target_destination[0]
                    end_node = nearest_point(target_dest, GLOBAL_VALID_POINTS)
                    start_node = nearest_point(car_pos_mm, GLOBAL_VALID_POINTS)
                    route_car_1 = calculate_optimal_route(GLOBAL_GRAPH, start_node, end_node)

                    if route_car_1 is not None:
                        pathLen = len(route_car_1)
                        lastNode = route_car_1[pathLen - 1]
                        if calculateDistance(route_car_1[pathLen - 2], target_dest) > calculateDistance(route_car_1[pathLen - 2], lastNode):
                            route_car_1.append(target_dest)
                        else:
                            route_car_1[pathLen - 1] = target_dest
                        # Force the first waypoint to be exactly the car's current mm position to avoid UNREACHABLE
                        route_car_1[0] = (car_1_state.position_mm[0], car_1_state.position_mm[1])
                    else:
                        # If no path, start route from current mm position to target
                        route_car_1 = [(car_1_state.position_mm[0], car_1_state.position_mm[1]), target_dest]

                    if route_car_1:
                        print(f"Route calculated with {len(route_car_1)} waypoints")
                    else:
                        print("No route found!")
                        route_car_1 = []
                    time.sleep(0.06)
                    success = client.update_car_route(Car_1_ID, route_car_1, userName, password, timeout=5.0)
                    if success:
                        print("✓ Route update successful!")
                        time.sleep(0.5)
                        updated_state = client.get_car_state(Car_1_ID, timeout=5.0)
                        if updated_state and updated_state.route:
                            print(f"✓ Verified: Car now has {len(updated_state.route)} route points")
                            car_1_Request_Calculate_Route_Flg = False
                        else:
                            print("⚠ Warning: Could not verify route update")
                    else:
                        print("✗ Route update failed!")

                # ==== Car 2 logic ====
                if car_2_Request_Pickup_Package_Flg:
                    # Hub position from any package's position_start[0]
                    try:
                        any_pkg2 = next(iter(Package_List.values()))
                        nearest_entrance2 = nearest_hub_entrance((car_2_state.position[0], car_2_state.position[1]), any_pkg2)
                        if nearest_entrance2 is not None:
                            dest2_x, dest2_y = nearest_entrance2[0], nearest_entrance2[1]
                        else:
                            dest2_x, dest2_y = any_pkg2["position_start"][0]
                    except Exception:
                        any_pkg2 = next(iter(Package_List.values()))
                        dest2_x, dest2_y = any_pkg2["position_start"][0]
                    distance2 = calculateDistance(car_2_state.position, (dest2_x, dest2_y))
                    if distance2 <= 36:
                        car2_pos = (car_2_state.position[0], car_2_state.position[1])
                        hub2_pos = (dest2_x, dest2_y)
                        # Clear any navigation-only destinations before pickup
                        car_2_target_destination = []
                        car_2_delivery_queue = []
                        # Phase 2: Rolling capacity pickup for Car 2
                        initial_owned2 = car_2_num_owned_package
                        car_2_owned_ids, car_2_target_destination, car_2_num_owned_package = rolling_capacity_pickup(
                            client, Car_2_ID, car2_pos, hub2_pos,
                            car_2_owned_ids, car_2_target_destination, car_2_num_owned_package,
                            max_capacity=3, user=userName, pwd=password
                        )
                        
                        if car_2_num_owned_package >= 3:
                            car_2_Request_Pickup_Package_Flg = False
                        
                        if car_2_num_owned_package > initial_owned2 and car_2_num_owned_package > 0:
                            print("Car2 recomputing TSP after rolling capacity pickup...")
                            tsp_idx_order2 = tsp_order(car2_pos, car_2_target_destination, GLOBAL_GRAPH, GLOBAL_VALID_POINTS)
                            car_2_delivery_queue = [car_2_target_destination[i] for i in tsp_idx_order2]
                            print(f"Car2 updated TSP queue: {car_2_delivery_queue}")
                            car_2_Request_Calculate_Route_Flg = True
                    else:
                        print("Car2 far from Hub, go to Hub first")
                        car_2_target_destination = [(dest2_x, dest2_y)]
                        car_2_Request_Calculate_Route_Flg = True

                    # Note: Pickup verification and TSP computation now handled within rolling_capacity_pickup for Car 2

                # Car 2 Delivery monitoring
                if car_2_state.numOwnedPackages == (car_2_num_owned_package - 1):
                    print(f"✓ Car {Car_2_ID} successfully delivered a package")
                    car_2_num_owned_package -= 1
                    if car_2_delivery_queue:
                        delivered_dest2 = car_2_delivery_queue.pop(0)
                        try:
                            car_2_target_destination.remove(delivered_dest2)
                        except ValueError:
                            pass
                    else:
                        if car_2_target_destination:
                            car_2_target_destination.pop(0)
                    
                    # Phase 2: Opportunistic refill for Car 2 - only if no more deliveries pending
                    if car_2_num_owned_package < 3 and len(car_2_target_destination) == 0:
                        try:
                            any_pkg2 = next(iter(Package_List.values()))
                            nearest_entrance2 = nearest_hub_entrance(
                                (car_2_state.position[0], car_2_state.position[1]), any_pkg2)
                            if nearest_entrance2:
                                hub_dist2 = calculateDistance(car_2_state.position, nearest_entrance2)
                                if hub_dist2 <= 36:
                                    print(f"🔄 Opportunistic refill: Car 2 near hub after delivery (dist={hub_dist2:.1f}mm)")
                                    car2_pos = (car_2_state.position[0], car_2_state.position[1])
                                    hub2_pos = (nearest_entrance2[0], nearest_entrance2[1])
                                    initial_owned2 = car_2_num_owned_package
                                    car_2_owned_ids, car_2_target_destination, car_2_num_owned_package = rolling_capacity_pickup(
                                        client, Car_2_ID, car2_pos, hub2_pos,
                                        car_2_owned_ids, car_2_target_destination, car_2_num_owned_package,
                                        max_capacity=3, user=userName, pwd=password
                                    )
                                    if car_2_num_owned_package > initial_owned2:
                                        tsp_idx_order2 = tsp_order(car2_pos, car_2_target_destination, GLOBAL_GRAPH, GLOBAL_VALID_POINTS)
                                        car_2_delivery_queue = [car_2_target_destination[i] for i in tsp_idx_order2]
                                        print(f"Car2 updated TSP queue after refill: {car_2_delivery_queue}")
                        except StopIteration:
                            pass
                    
                    # Always set route flag if there are still destinations pending
                    if len(car_2_target_destination) > 0:
                        car_2_Request_Calculate_Route_Flg = True
                    if len(car_2_target_destination) == 0:
                        car_2_target_destination = []
                        car_2_Request_Pickup_Package_Flg = True
                        car_2_Request_Calculate_Route_Flg = False
                        car_2_owned_ids = []

                # Car 2 Delivery routing (using pre-built graph)
                if car_2_Request_Calculate_Route_Flg and len(car_2_target_destination) > 0:
                    car2_pos_mm = (car_2_state.position_mm[0], car_2_state.position_mm[1])
                    if car_2_delivery_queue:
                        target_dest2 = car_2_delivery_queue[0]
                    else:
                        target_dest2 = car_2_target_destination[0]
                    end_node2 = nearest_point(target_dest2, GLOBAL_VALID_POINTS)
                    start_node2 = nearest_point(car2_pos_mm, GLOBAL_VALID_POINTS)
                    route_car_2 = calculate_optimal_route(GLOBAL_GRAPH, start_node2, end_node2)

                    if route_car_2 is not None:
                        pathLen2 = len(route_car_2)
                        lastNode2 = route_car_2[pathLen2 - 1]
                        if calculateDistance(route_car_2[pathLen2 - 2], target_dest2) > calculateDistance(route_car_2[pathLen2 - 2], lastNode2):
                            route_car_2.append(target_dest2)
                        else:
                            route_car_2[pathLen2 - 1] = target_dest2
                        # Force the first waypoint to be exactly the car's current mm position to avoid UNREACHABLE
                        route_car_2[0] = (car_2_state.position_mm[0], car_2_state.position_mm[1])
                    else:
                        # If no path, start route from current mm position to target
                        route_car_2 = [(car_2_state.position_mm[0], car_2_state.position_mm[1]), target_dest2]

                    if route_car_2:
                        print(f"Car2 route calculated with {len(route_car_2)} waypoints")
                    else:
                        print("Car2: No route found!")
                        route_car_2 = []
                    time.sleep(0.06)
                    success2 = client.update_car_route(Car_2_ID, route_car_2, userName, password, timeout=5.0)
                    if success2:
                        print("✓ Car2 Route update successful!")
                        time.sleep(0.5)
                        updated_state2 = client.get_car_state(Car_2_ID, timeout=5.0)
                        if updated_state2 and updated_state2.route:
                            print(f"✓ Verified: Car2 now has {len(updated_state2.route)} route points")
                            car_2_Request_Calculate_Route_Flg = False
                        else:
                            print("⚠ Warning: Could not verify Car2 route update")
                    else:
                        print("✗ Car2 Route update failed!")

            # Team info
            if loop_count % 3 == 0:
                time.sleep(0.06)
                team_result = client.get_teams_information()
                if team_result is not None:
                    success, team_info = team_result
                    print("\n=== Team Information ===")
                    if success and userName in team_info:
                        info = team_info[userName]
                        print(f"Team Name: {userName}")
                        print(f"Score: {info['point']}")
                        print(f"Travel Distance: {info['travel_distance']}")

            # Adaptive sleep: faster polling during active delivery
            if (car_1_state.numOwnedPackages > 0 and len(car_1_target_destination) > 0) or (car_2_state.numOwnedPackages > 0 and len(car_2_target_destination) > 0):
                time.sleep(0.4)
            else:
                time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n\n=== Monitoring stopped by user ===")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    client.disconnect()
    print("\n=== V4 Standalone Complete ===")


if __name__ == "__main__":
    main()
