import socketio
import numpy as np
import threading
import time
from typing import Dict, Optional, Callable
from .models import CarState
import requests
import os

class LocalizationAPIClient:
    """Socket.IO client to interact with the Localization API server"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8080):
        self.server_host = server_host
        self.server_port = server_port
        self.server_url = f'http://{self.server_host}:{self.server_port}'
        self.sio = socketio.Client()
        self.is_connected = False
        self.response_data = {}
        self.response_event = threading.Event()
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            self.is_connected = True
            
        @self.sio.event
        def disconnect():
            print("Disconnected from server")
            self.is_connected = False

        @self.sio.event
        def server_init_status(data):
            """Handle car data response"""
            self.response_data['server_init_status'] = data
            self.response_event.set()

        @self.sio.event
        def get_assign_car(data):
            """Handle response"""
            self.response_data['get_assign_car'] = data
            self.response_event.set()
            
        @self.sio.event
        def car_data(data):
            """Handle car data response"""
            self.response_data['car_data'] = data
            self.response_event.set()

        @self.sio.event
        def route_updated(data):
            """Handle route update response"""
            self.response_data['route_updated'] = data
            self.response_event.set()

        @self.sio.event
        def package_updated(data):
            """Handle package_updated response"""
            self.response_data['package_updated'] = data
            self.response_event.set()
        
        @self.sio.event
        def road_information(data):
            """Handle get road information response"""
            self.response_data['road_information'] = data
            self.response_event.set()
        
        @self.sio.event
        def teams_information(data):
            """Handle get teams information response"""
            self.response_data['teams_information'] = data
            self.response_event.set()

        @self.sio.event
        def package_data(data):
            """Handle get road information response"""
            self.response_data['package_data'] = data
            self.response_event.set()
            
        @self.sio.event
        def health_status(data):
            """Handle health check response"""
            self.response_data['health_status'] = data
            self.response_event.set()
        
        @self.sio.event
        def team_information_updated(data):
            """Handle health check response"""
            self.response_data['team_information_updated'] = data
            self.response_event.set()

        @self.sio.event
        def error(data):
            """Handle error response"""
            self.response_data['error'] = data
            self.response_event.set()
                
        @self.sio.event
        def car_updated(data):
            """Handle single car update"""
            if hasattr(self, 'on_car_updated') and self.on_car_updated:
                self.on_car_updated(data)
                
        @self.sio.event
        def car_route_changed(data):
            """Handle route change broadcasts"""
            if hasattr(self, 'on_route_changed') and self.on_route_changed:
                self.on_route_changed(data)
    
    def connect(self, userName, password) -> bool:
        """
        Establishes a connection to the Localization API server using the provided username and password.
        Attempts to connect to the server and emits team information for authentication.
        Waits for a response indicating whether the connection and authentication were successful.
        Args:
            userName (str): The username to authenticate with the server.
            password (str): The password to authenticate with the server.
        Returns:
            bool: True if connected and authenticated successfully, False otherwise.
        Raises:
            Prints error messages to the console if connection or authentication fails.
        """
        try:
            self.sio.connect(self.server_url) 
            # Wait a moment for connection to establish
            time.sleep(0.1)
            try:
                self.sio.emit('push_team_information', {
                    'userName': userName,
                    'pwd': password
                })
                response = self._wait_for_response(3.0)

                if 'team_information_updated' in response:
                    print("Connected to Localization API server")
                    return self.is_connected
                elif 'error' in response:
                    print(f"Failed to connect to Localization API server: {response['error']['message']}")
                    return False
                else:
                    print("No response received")
                    return False
                    
            except Exception as e:
                print(f"Request error: {e}")
                return False
            
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """
        Disconnects the client from the server if currently connected.
        This method checks the connection status and, if connected, 
        disconnects the client using the socket.io interface.
        """
        if self.is_connected:
            self.sio.disconnect()
    
    def _wait_for_response(self, timeout: float = 1.0) -> Dict:
        """
        Waits for a response event within a specified timeout period.
        Clears the response event and response data before waiting. If the response event is set within the timeout,
        returns a copy of the response data. Otherwise, returns an error dictionary indicating a request timeout.
        Args:
            timeout (float, optional): Maximum time to wait for the response event in seconds. Defaults to 1.0.
        Returns:
            Dict: A copy of the response data if the event is set, or an error dictionary if the timeout occurs.
        """
        self.response_event.clear()
        self.response_data.clear()
        
        if self.response_event.wait(timeout):
            return self.response_data.copy()
        else:
            return {'error': {'message': 'Request timeout'}}
    
    def get_server_status(self,  timeout: float = 1.0):
        """
        Retrieves the server's initialization status.
        Emits a 'get_server_init_status' event to the server and waits for a response.
        Returns the server's initialization state if available, or None if not connected,
        an error occurs, or no response is received.
        Args:
            timeout (float, optional): Maximum time in seconds to wait for the server response. Defaults to 1.0.
        Returns:
            int or None: The server's initialization state (typically 1 if initialization is complete),
            or None if not connected, an error occurs, or no response is received.
        """
        if not self.is_connected:
            print("Not connected to server")
            return None  
        try:
            self.sio.emit('get_server_init_status', {})
            response = self._wait_for_response(timeout)      
            if 'server_init_status' in response:
                status = response['server_init_status']['state'] # Return 1 if finish intialize
                return status
            elif 'error' in response:
                print(f"Error getting data from Server: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
        
    def get_assign_car(self,  timeout: float = 1.0):
        """
        Requests assigned car IDs from the server.
        Emits a 'get_assign_car' event to the server and waits for a response within the specified timeout.
        If successful, returns a tuple containing the IDs of two assigned cars.
        Handles connection errors, server errors, and timeouts gracefully.
        Args:
            timeout (float, optional): Maximum time to wait for a response from the server in seconds. Defaults to 1.0.
        Returns:
            tuple or None: A tuple (CAR_1_ID, CAR_2_ID) if successful, or None if an error occurs or no response is received.
        """
        if not self.is_connected:
            print("Not connected to server")
            return None  
        try:
            self.sio.emit('get_assign_car', {})
            response = self._wait_for_response(timeout)      
            if 'get_assign_car' in response:
                CAR_1_ID = response['get_assign_car']['car_id'][0]
                CAR_2_ID = response['get_assign_car']['car_id'][1]
                return CAR_1_ID, CAR_2_ID
            elif 'error' in response:
                print(f"Error getting data from Server: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_car_state(self, car_id: int, timeout: float = 1.0) -> Optional[CarState]:
        """
        Retrieves the current state of a car from the server.
        Args:
            car_id (int): The unique identifier of the car whose state is to be retrieved.
            timeout (float, optional): The maximum time in seconds to wait for a response from the server. Defaults to 1.0.
        Returns:
            Optional[CarState]: An instance of CarState containing the car's state if successful, or None if an error occurs or no response is received.
        Raises:
            Exception: If an unexpected error occurs during the request.
        Notes:
            - Prints an error message if not connected to the server, if an error is received in the response, or if no response is received.
        """
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_car', {'car_id': car_id})
            response = self._wait_for_response(timeout)
            
            if 'car_data' in response:
                data = response['car_data']['data']
                return CarState(
                    id=data['id'],
                    position=np.array(data['position']) if data.get('position') is not None else np.array([0, 0]),
                    position_mm=np.array(data['position_mm']),
                    orientation=data['orientation'],
                    speed_mm_per_s=data['speed_mm_per_s'],
                    obstacles_abs=[(dist, angle) for dist, angle in data['obstacles_abs']],
                    control_command=data['control_command'],
                    desired_angle=data['desired_angle'],
                    route=[(x, y) for x, y in data['route']],
                    numOwnedPackages=data['numOwnedPackages'],
                    timestamp=data['timestamp']
                )
            elif 'error' in response:
                print(f"Error getting car state: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_road_information(self,  timeout: float = 1.0):
        """
        Retrieves road information from the server.
        Emits a 'get_road_information' event to the server and waits for a response.
        Returns a tuple containing the success status, list of streets, and list of points if successful.
        If an error occurs or no response is received, prints an error message and returns None.
        Args:
            timeout (float, optional): Maximum time to wait for a response in seconds. Defaults to 1.0.
        Returns:
            tuple or None: (success, streets, points) if successful, otherwise None.
        """
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_road_information', {})
            response = self._wait_for_response(timeout)         
            if 'road_information' in response:
                streets = response['road_information']['streets']
                points = response['road_information']['points']
                success = response['road_information']['success']
                return success, streets, points
            elif 'error' in response:
                print(f"Error getting road information: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_teams_information(self,  timeout: float = 1.0):
        """
        Retrieves information about teams from the server.
        Emits a 'get_teams_information' event to the server and waits for a response.
        Returns a tuple (success, info) if the response contains team information.
        If an error occurs or no response is received, prints an error message and returns None.
        Args:
            timeout (float, optional): Time in seconds to wait for a response. Defaults to 1.0.
        Returns:
            tuple or None: (success, info) if successful, None otherwise.
        """
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_teams_information', {})
            response = self._wait_for_response(timeout)
   
            if 'teams_information' in response:
                info = response['teams_information']['info']
                success = response['teams_information']['success']
                return success, info
            elif 'error' in response:
                print(f"Error getting teams information: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_package_list(self, timeout: float = 1.0):
        """
        Retrieves the list of packages from the server.
        Args:
            timeout (float, optional): The maximum time to wait for a response from the server, in seconds. Defaults to 1.0.
        Returns:
            tuple:
                - success (bool): True if the package list was retrieved successfully, False otherwise.
                - data (list or None): The list of packages if successful, None otherwise.
        Notes:
            - If not connected to the server, returns None.
            - If an error occurs or no response is received, returns (False, None).
            - Prints error messages to the console in case of failure.
        """
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_package_list', {})
            response = self._wait_for_response(timeout)
            
            if 'package_data' in response:
                data = response['package_data']['packages']
                success = response['package_data']['success']
                return success, data
            elif 'error' in response:
                print(f"Error getting package list: {response['error']['message']}")
                return False, None
            else:
                print("No response received")
                return False, None
                
        except Exception as e:
            print(f"Request error: {e}")
            return False, None

    def update_car_route(self, car_id: int, new_route: list, userName: str = '', password: str = '', timeout: float = 1.0) -> bool:
        """
        Updates the route for a specified car by emitting an 'update_route' event to the server.
        Args:
            car_id (int): The unique identifier of the car whose route is to be updated.
            new_route (list): The new route to assign to the car.
            userName (str, optional): Username for authentication. Defaults to ''.
            password (str, optional): Password for authentication. Defaults to ''.
            timeout (float, optional): Time in seconds to wait for a server response. Defaults to 1.0.
        Returns:
            bool: True if the route was successfully updated, False otherwise.
        Raises:
            Exception: If an error occurs during the request.
        """
        if not self.is_connected:
            print("Not connected to server")
            return False
        
        try:
            self.sio.emit('update_route', {
                'car_id': car_id,
                'route': new_route,
                'userName': userName,
                'pwd': password
            })
            response = self._wait_for_response(timeout)
            
            if 'route_updated' in response:
                print(f"Successfully updated route for car {car_id}")
                return True
            elif 'error' in response:
                print(f"Failed to update route: {response['error']['message']}")
                return False
            else:
                print("No response received")
                return False
                
        except Exception as e:
            print(f"Request error: {e}")
            return False
        
    def request_pickup_package(self, car_id: int, package_id: int, userName: str = '', password: str = '', timeout: float = 1.0):
        """
        Sends a request to pick up a package using the specified car.
        Args:
            car_id (int): The ID of the car that will pick up the package.
            package_id (int): The ID of the package to be picked up.
            userName (str, optional): Username for authentication. Defaults to ''.
            password (str, optional): Password for authentication. Defaults to ''.
            timeout (float, optional): Time in seconds to wait for a response. Defaults to 1.0.
        Returns:
            bool: True if the package was successfully picked up, False otherwise.
        Raises:
            Exception: If an error occurs during the request process.
        """
        if not self.is_connected:
            print("Not connected to server")
            return False
        
        try:
            self.sio.emit('request_pickup_package', {
                'car_id': car_id,
                'package_id': package_id,
                'userName': userName,
                'pwd': password
            })
            response = self._wait_for_response(timeout)
            
            if 'package_updated' in response:
                print(f"Successfully pick up package {package_id} for car {car_id}")
                return True
            elif 'error' in response:
                print(f"Failed to pick up package: {response['error']['message']}")
                return False
            else:
                print("No response received")
                return False
                
        except Exception as e:
            print(f"Request error: {e}")
            return False

def create_client(server_url: str) -> LocalizationAPIClient:
    """Factory function to create a LocalizationAPIClient"""
    if '://' in server_url:
        # Remove protocol if present
        server_url = server_url.split('://', 1)[1]
    
    if ':' in server_url:
        host, port = server_url.split(':')
        return LocalizationAPIClient(server_host=host, server_port=int(port))
    else:
        return LocalizationAPIClient(server_host=server_url)
