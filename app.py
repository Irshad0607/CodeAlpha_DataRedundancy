import os
import hashlib
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE", "RedundancyDB")
CONTAINER_NAME = os.getenv("COSMOS_CONTAINER", "Records")


def get_cosmos_container():
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.create_database_if_not_exists(id=DATABASE_NAME)
    container = database.create_container_if_not_exists(
        id=CONTAINER_NAME,
        partition_key=PartitionKey(path="/record_hash"),
        offer_throughput=None
    )
    return container


def generate_hash(data_dict):
    sorted_data = json.dumps(data_dict, sort_keys=True).lower().strip()
    hash_object = hashlib.sha256(sorted_data.encode('utf-8'))
    return hash_object.hexdigest()


def is_duplicate(container, record_hash):
    try:
        query = f"SELECT * FROM c WHERE c.record_hash = '{record_hash}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return len(items) > 0
    except Exception as e:
        print(f"Error checking duplicate: {e}")
        return False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/submit', methods=['POST'])
def submit_data():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data received."}), 400

        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        clean_data = {
            "name": data.get("name", "").strip(),
            "email": data.get("email", "").strip().lower(),
            "phone": data.get("phone", "").strip().replace(" ", "").replace("-", ""),
            "address": data.get("address", "").strip().lower(),
            "notes": data.get("notes", "").strip().lower()
        }

        hash_data = {k: v for k, v in clean_data.items() if v}
        record_hash = generate_hash(hash_data)
        container = get_cosmos_container()

        if is_duplicate(container, record_hash):
            return jsonify({
                "status": "duplicate",
                "classification": "REDUNDANT",
                "message": "Duplicate entry detected. This record already exists in the database.",
                "hash": record_hash[:16] + "...",
                "data_received": clean_data
            }), 409

        record_id = f"record_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        new_record = {
            "id": record_id,
            "record_hash": record_hash,
            "classification": "UNIQUE",
            "data": clean_data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "WebForm"
        }

        container.create_item(body=new_record)

        return jsonify({
            "status": "success",
            "classification": "UNIQUE",
            "message": "Record is unique. Successfully saved to database.",
            "record_id": record_id,
            "hash": record_hash[:16] + "...",
            "data_saved": clean_data,
            "timestamp": new_record["timestamp"]
        }), 201

    except exceptions.CosmosHttpResponseError as e:
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500


@app.route('/api/records', methods=['GET'])
def get_records():
    try:
        container = get_cosmos_container()
        query = "SELECT c.id, c.record_hash, c.classification, c.data, c.timestamp FROM c ORDER BY c.timestamp DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return jsonify({"status": "success", "total_records": len(items), "records": items}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/delete/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    try:
        record_hash = request.args.get('record_hash')
        if not record_hash:
            return jsonify({"status": "error", "message": "record_hash query parameter is required."}), 400

        container = get_cosmos_container()
        container.delete_item(item=record_id, partition_key=record_hash)

        return jsonify({"status": "success", "message": f"Record {record_id} deleted successfully."}), 200

    except exceptions.CosmosResourceNotFoundError:
        return jsonify({"status": "error", "message": "Record not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/clear', methods=['DELETE'])
def clear_records():
    try:
        container = get_cosmos_container()
        items = list(container.query_items(query="SELECT c.id, c.record_hash FROM c", enable_cross_partition_query=True))
        deleted_count = 0
        for item in items:
            container.delete_item(item=item['id'], partition_key=item['record_hash'])
            deleted_count += 1
        return jsonify({"status": "success", "message": f"Cleared {deleted_count} records from database."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "application": "Data Redundancy Removal System", "version": "1.0.0"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)