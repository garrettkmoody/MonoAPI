from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)

load_dotenv()

@app.route('/flights/<string:flight_number>/<string:date>', methods=['GET'])
def get_flight(flight_number, date=None):
    try:
        url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number}/{date}"
        
        params = {"withLocation": "true"}
        headers = {
            "x-rapidapi-key": os.getenv('RAPID_API_KEY'),
            "x-rapidapi-host": os.getenv('RAPID_API_HOST')
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch flight data: {str(e)}"}), 503
    except ValueError:
        return jsonify({"error": "Invalid response from aviation API"}), 502

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

