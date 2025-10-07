from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone

app = Flask(__name__)

load_dotenv()

def calculate_time_until_landing(flight):
    """Calculate time remaining until landing if live data is available"""
    try:
        arrival = flight.get('arrival', {})
        
        # Priority: actual time > predicted time > scheduled time
        arrival_time_utc = (
            arrival.get('actualTime', {}).get('utc') if arrival.get('actualTime') else
            arrival.get('predictedTime', {}).get('utc') if arrival.get('predictedTime') else
            arrival.get('scheduledTime', {}).get('utc')
        )
        
        if not arrival_time_utc:
            return None
        
        # Parse the time (format: "2025-10-05 13:38Z")
        arrival_dt = datetime.strptime(arrival_time_utc, "%Y-%m-%d %H:%MZ").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        time_diff = arrival_dt - now
        
        # If flight has already landed (negative time)
        if time_diff.total_seconds() < 0:
            return {
                "minutes": 0,
                "hours": 0,
                "status": "landed",
                "message": "Flight has landed"
            }
        
        # Calculate hours and minutes
        total_minutes = int(time_diff.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        return {
            "minutes": minutes,
            "hours": hours,
            "total_minutes": total_minutes,
            "status": "in_flight",
            "message": f"{hours}h {minutes}m until landing"
        }
    except Exception as e:
        print(f"Error calculating time until landing: {e}")
        return None

def enrich_flight_data(flight):
    """Add calculated fields like time until landing"""
    enriched = flight.copy()
    
    # Add time until landing
    time_until_landing = calculate_time_until_landing(flight)
    if time_until_landing:
        enriched['time_until_landing'] = time_until_landing
    
    return enriched

@app.route('/flights/<string:flight_number>/<string:date>', methods=['GET'])
def get_flight(flight_number, date=None):
    try:
        # Check if single flight filter is requested
        single_flight = request.args.get('single', 'false').lower() == 'true'
        
        url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number}/{date}"
        
        params = {"withLocation": "true"}
        headers = {
            "x-rapidapi-key": os.getenv('RAPID_API_KEY'),
            "x-rapidapi-host": os.getenv('RAPID_API_HOST')
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        flight_data = response.json()
        
        # If single=true, filter to match departure date
        if single_flight and isinstance(flight_data, list):
            # Parse the requested date
            requested_date = date  # Format: YYYY-MM-DD
            
            for flight in flight_data:
                departure_time = flight.get('departure', {}).get('scheduledTime', {}).get('local', '')
                
                # Extract date from departure time (format: "2025-10-04 23:59-08:00")
                if departure_time:
                    try:
                        # Extract just the date part (YYYY-MM-DD)
                        flight_date = departure_time.split(' ')[0]
                        
                        if flight_date == requested_date:
                            # Enrich with calculated data
                            enriched_flight = enrich_flight_data(flight)
                            return jsonify(enriched_flight), 200
                    except Exception as e:
                        print(f"Error parsing date: {e}")
                        continue
            
            # If no matching flight found, return error
            return jsonify({"error": f"No flight found with departure date {requested_date}"}), 404
        
        # Enrich all flights in array
        if isinstance(flight_data, list):
            enriched_data = [enrich_flight_data(flight) for flight in flight_data]
            return jsonify(enriched_data), response.status_code
        else:
            enriched_data = enrich_flight_data(flight_data)
            return jsonify(enriched_data), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch flight data: {str(e)}"}), 503
    except ValueError:
        return jsonify({"error": "Invalid response from aviation API"}), 502

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

