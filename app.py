import json
import os
import uuid
from datetime import datetime

from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

app = Flask(__name__)

# --- Persistence Configuration ---
EVENTS_FILE = 'events.json'

def load_events():
    """
    Loads events from the JSON file.
    Converts 'start_time' and 'end_time' strings to datetime objects.
    Assigns a unique ID if an event loaded from file doesn't have one.
    Handles file not found or JSON decoding errors gracefully.
    """
    if not os.path.exists(EVENTS_FILE) or os.stat(EVENTS_FILE).st_size==0:
        return [] # Return empty list if file doesn't exist or is empty
    
    try:
        with open(EVENTS_FILE, 'r') as f:
            events_data = json.load(f)
            # Ensure each event has an ID and convert time strings back to datetime objects
            for event in events_data:
                if 'id' not in event: # Assign ID if missing (for backward compatibility)
                    event['id'] = str(uuid.uuid4())
                try:
                    event['start_time'] = datetime.fromisoformat(event['start_time'])
                    event['end_time'] = datetime.fromisoformat(event['end_time'])
                except (ValueError, TypeError) as e:
                    print(f"Warning: Malformed time data in event ID {event.get('id', 'N/A')}: {e}")
                    # If time data is malformed, you might want to handle it specifically,
                    # e.g., set to None or a default, or skip the event.
            return events_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {EVENTS_FILE}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading events: {e}")
        return []

def save_events(events):
    """
    Saves events to the JSON file.
    Converts datetime objects to ISO format strings for JSON serialization.
    Handles potential file writing errors.
    """
    try:
        serializable_events = []
        for event in events:
            serializable_event = event.copy()
            # Convert datetime objects to ISO format strings
            if isinstance(serializable_event.get('start_time'), datetime):
                serializable_event['start_time'] = serializable_event['start_time'].isoformat()
            if isinstance(serializable_event.get('end_time'), datetime):
                serializable_event['end_time'] = serializable_event['end_time'].isoformat()
            serializable_events.append(serializable_event)
        
        with open(EVENTS_FILE, 'w') as f:
            json.dump(serializable_events, f, indent=4)
    except TypeError as e:
        print(f"Error during JSON serialization (possible non-serializable data): {e}")
        raise InternalServerError("Failed to save events due to data serialization error.")
    except IOError as e:
        print(f"Error writing to file {EVENTS_FILE}: {e}")
        raise InternalServerError("Failed to save events due to file system error.")
    except Exception as e:
        print(f"An unexpected error occurred while saving events: {e}")
        raise InternalServerError("Failed to save events due to an unexpected error.")


# Load events when the application starts
events = load_events()

# --- Helper Functions ---
def validate_event_data(data, is_update=False):
    """
    Validates incoming event data for creation or update.
    Returns (True, None) for valid data, or (False, error_messages_list) for invalid data.
    `is_update` allows partial data for PUT requests.
    """
    errors = []
    
    # For creation, all required fields must be present
    if not is_update:
        required_fields = ['title', 'description', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: '{field}'")
    
    # Validate title if present
    if 'title' in data:
        if not isinstance(data['title'], str) or not data['title'].strip():
            errors.append("Title must be a non-empty string.")
            
    # Validate description if present
    if 'description' in data:
        if not isinstance(data['description'], str):
            errors.append("Description must be a string.")

    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    # Validate and parse start_time if present
    parsed_start_time = None
    if start_time_str is not None:
        if not isinstance(start_time_str, str):
            errors.append("start_time must be a string.")
        else:
            try:
                parsed_start_time = datetime.fromisoformat(start_time_str)
            except ValueError:
                errors.append("Invalid start_time format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS).")

    # Validate and parse end_time if present
    parsed_end_time = None
    if end_time_str is not None:
        if not isinstance(end_time_str, str):
            errors.append("end_time must be a string.")
        else:
            try:
                parsed_end_time = datetime.fromisoformat(end_time_str)
            except ValueError:
                errors.append("Invalid end_time format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS).")
    
    # Return parsed times alongside validity status for convenience
    return len(errors)==0, errors, parsed_start_time, parsed_end_time

def get_event_by_id(event_id):
    """Finds an event by its ID in the global events list."""
    for event in events:
        if event['id']==event_id:
            return event
    return None

# --- Custom Error Handlers ---
@app.errorhandler(400)
def bad_request_error(error):
    """Handles 400 Bad Request errors."""
    return jsonify({"error": "Bad Request", "message": error.description}), 400

@app.errorhandler(404)
def not_found_error(error):
    """Handles 404 Not Found errors."""
    return jsonify({"error": "Not Found", "message": error.description}), 404

@app.errorhandler(500)
def internal_server_error(error):
    """Handles 500 Internal Server Error."""
    # In a production environment, you would log the full exception details
    # For now, we print to console.
    print(f"Internal Server Error: {error}") 
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred on the server."}), 500

# --- API Endpoints ---

@app.route('/')
def home():
    """Root endpoint for the API."""
    return jsonify({"message": "Welcome to the Event Scheduler API! Use /events to manage events."}), 200

@app.route('/events', methods=['POST'])
def create_event():
    """
    Creates a new event.
    Requires title, description, start_time, and end_time in ISO 8601 format.
    Returns 201 Created on success, 400 Bad Request on validation error.
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Request body must be JSON.")

        is_valid, errors, parsed_start_time, parsed_end_time = validate_event_data(data, is_update=False)
        if not is_valid:
            raise BadRequest(", ".join(errors))
        
        # Additional check for full time validation on creation as both times must be present
        if parsed_start_time >= parsed_end_time:
            raise BadRequest("Start time must be strictly before end time.")

        new_event = {
            'id': str(uuid.uuid4()),  # Generate a unique ID
            'title': data['title'].strip(),
            'description': data['description'].strip(),
            'start_time': parsed_start_time,
            'end_time': parsed_end_time
        }
        
        events.append(new_event)
        save_events(events) # Persist the new event

        # Prepare response (convert datetime objects back to string for JSON)
        response_event = new_event.copy()
        response_event['start_time'] = response_event['start_time'].isoformat()
        response_event['end_time'] = response_event['end_time'].isoformat()

        return jsonify({"message": "Event created successfully", "event": response_event}), 201

    except BadRequest as e:
        return jsonify({"error": "Bad Request", "message": e.description}), 400
    except Exception as e:
        print(f"Error creating event: {e}") # Log the actual error
        raise InternalServerError("An unexpected error occurred while creating the event.")


@app.route('/events', methods=['GET'])
def list_events():
    """
    Retrieves all scheduled events, sorted by start_time (earliest first).
    Returns 200 OK.
    """
    try:
        # Sort events by start_time
        sorted_events = sorted(events, key=lambda event: event['start_time'])
        
        # Prepare events for JSON response (convert datetime objects to string)
        response_events = []
        for event in sorted_events:
            response_event = event.copy()
            response_event['start_time'] = response_event['start_time'].isoformat()
            response_event['end_time'] = response_event['end_time'].isoformat()
            response_events.append(response_event)

        return jsonify({"events": response_events}), 200
    except Exception as e:
        print(f"Error listing events: {e}") # Log the actual error
        raise InternalServerError("An unexpected error occurred while listing events.")


@app.route('/events/<string:event_id>', methods=['PUT'])
def update_event(event_id):
    """
    Updates an existing event identified by event_id.
    Allows partial updates of title, description, start_time, and end_time.
    Returns 200 OK on success, 400 Bad Request on validation error, 404 Not Found if event doesn't exist.
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Request body must be JSON.")

        # Validate incoming data, allowing partial updates.
        # This will return parsed_start_time and parsed_end_time only if they were in the request.
        is_valid, errors, parsed_req_start_time, parsed_req_end_time = validate_event_data(data, is_update=True)
        if not is_valid:
            raise BadRequest(", ".join(errors))

        # Find the event by ID
        event_index = -1
        for i, event in enumerate(events):
            if event['id']==event_id:
                event_to_update = event
                event_index = i
                break
        
        if event_index==-1:
            raise NotFound(f"Event with ID '{event_id}' not found.")

        # Apply updates from the request data
        if 'title' in data:
            event_to_update['title'] = data['title'].strip()
        if 'description' in data:
            event_to_update['description'] = data['description'].strip()
        
        # Update times only if they were provided in the request AND successfully parsed
        if parsed_req_start_time:
            event_to_update['start_time'] = parsed_req_start_time
        if parsed_req_end_time:
            event_to_update['end_time'] = parsed_req_end_time
        
        # After potential updates, re-validate the time logic of the combined (new + old) times
        # This catches cases where one time was updated, making the event invalid
        if event_to_update['start_time'] >= event_to_update['end_time']:
            raise BadRequest("Updated start time must be strictly before updated end time.")

        # No need to explicitly replace, as event_to_update is a reference to the item in `events` list
        save_events(events) # Persist the updated event list

        # Prepare response (convert datetime objects back to string for JSON)
        response_event = event_to_update.copy()
        response_event['start_time'] = response_event['start_time'].isoformat()
        response_event['end_time'] = response_event['end_time'].isoformat()

        return jsonify({"message": "Event updated successfully", "event": response_event}), 200

    except BadRequest as e:
        return jsonify({"error": "Bad Request", "message": e.description}), 400
    except NotFound as e:
        return jsonify({"error": "Not Found", "message": e.description}), 404
    except Exception as e:
        print(f"Error updating event '{event_id}': {e}") # Log the actual error
        raise InternalServerError("An unexpected error occurred while updating the event.")


@app.route('/events/<string:event_id>', methods=['DELETE'])
def delete_event(event_id):
    #Deletes an event identified by event_id.
    #Returns 200 OK on success, 404 Not Found if event doesn't exist.
    
    global events # Declare 'events' as global to modify the list in place
    try:
        # Find the event by ID and its index
        event_index_to_delete = -1
        for i, event in enumerate(events):
            if event['id']==event_id:
                event_index_to_delete = i
                break
        
        if event_index_to_delete==-1:
            raise NotFound(f"Event with ID '{event_id}' not found.")

        # Remove the event from the list
        deleted_event = events.pop(event_index_to_delete)
        save_events(events) # Persist the updated event list

        return jsonify({"message": f"Event '{deleted_event['title']}' with ID '{event_id}' deleted successfully"}), 200

    except NotFound as e:
        return jsonify({"error": "Not Found", "message": e.description}), 404
    except Exception as e:
        print(f"Error deleting event '{event_id}': {e}") # Log the actual error
        raise InternalServerError("An unexpected error occurred while deleting the event.")


if __name__=='__main__':
    app.run(debug=True)
