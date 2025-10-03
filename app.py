from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)

#dotenv load
load_dotenv()
AVIATION_DATA_ENDPOINT = f"https://api.aviationstack.com/v1/flights?access_key={os.getenv('AVIATION_API_KEY')}"

def get_flight_data(airline: str, flight_number: int = None):
    response = requests.get(AVIATION_DATA_ENDPOINT)
    return response.json()
    return {
        "airline": airline,
        "flight_number": flight_number,
        "departure": "LAX",
        "arrival": "SFO",
    }

@app.route('/flights/<string:airline>/<int:flight_number>', methods=['GET'])
def get_flight(airline, flight_number):
    return jsonify(get_flight_data(airline, flight_number))

@app.route('/flights/<string:airline>', methods=['GET'])
def get_flights(airline):
    return jsonify(get_flight_data(airline, 123))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

