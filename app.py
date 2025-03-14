from flask import Flask, request, jsonify
import boto3
import uuid
import os
from configparser import ConfigParser, NoSectionError

class DynamoDBClient:
    """Handles DynamoDB operations."""
    def __init__(self, table_name):
        config = ConfigParser()
        this_folder = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(this_folder,'config.ini')
        config.read(config_path)
        try:
            self.AWS_ACCESS_KEY = config.get('aws','AWS_ACCESS_KEY')
            self.AWS_SECRET_ACCESS_KEY = config.get('aws', 'AWS_SECRET_ACCESS_KEY')
            self.REGION_NAME = config.get('aws', 'REGION_NAME')
        except NoSectionError as error:
            print(f"Configuration error: {error}")
            exit(1)

        """Initialize the DynamoDB client with AWS credentials and table name."""
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.REGION_NAME,  # Change as needed
            aws_access_key_id=self.AWS_ACCESS_KEY,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )
        self.table = self.dynamodb.Table(table_name)

    def store_data(self, data):
        """Stores data in DynamoDB with a unique ID."""
        data["id"] = str(uuid.uuid4())  # Generate a unique ID
        self.table.put_item(Item=data)
        return data["id"]

# Initialize Flask and DynamoDB client
app = Flask(__name__)
dynamodb_client = DynamoDBClient("employee_details")  # Change to your table name

@app.route("/store", methods=["POST"])
def store_data():
    """API endpoint to store data in DynamoDB."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid input, JSON required"}), 400

        item_id = dynamodb_client.store_data(data)
        return jsonify({"message": "Data stored successfully", "id": item_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
