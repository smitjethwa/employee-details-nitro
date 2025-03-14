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
            self.KMS_KEY_ID = config.get('aws', 'KMS_KEY_ID')
        except NoSectionError as error:
            print(f"Configuration error: {error}")
            exit(1)

        # Initialize the DynamoDB client with AWS credentials and table name 
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.REGION_NAME,  # Change as needed
            aws_access_key_id=self.AWS_ACCESS_KEY,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )
        self.table = self.dynamodb.Table(table_name)
        
        # KMS Client    
        self.kms_client = boto3.client("kms", region_name=self.REGION_NAME)

    def store_data(self, data):
        """Stores data in DynamoDB with a unique ID."""
        data["id"] = str(uuid.uuid4())  # Generate a unique ID
        self.table.put_item(Item=data)
        return data["id"]
    
    def fetch_data(self, item_id):
        """Fetches data from DynamoDB using the unique ID."""
        response = self.table.get_item(Key={"id": item_id})
        return response.get("Item")
    
    def encrypt_data(self,plain_text):
        response = self.kms_client.encrypt(KeyId=self.KMS_KEY_ID, Plaintext=plain_text.encode())
        return response["CiphertextBlob"]

    def decrypt_data(self,cipher_text):
        response = self.kms_client.decrypt(CiphertextBlob=cipher_text)
        return response["Plaintext"].decode()

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
        
        encrypted_mobile = dynamodb_client.encrypt_data(data["mobile"])
        encrypted_aadhaar = dynamodb_client.encrypt_data(data["aadhaar_number"])
        user_data = {
            "name": data["name"],
            "email": data["email"],
            "dob": data["dob"],
            "mobile": encrypted_mobile,
            "aadhaar_number": encrypted_aadhaar
        }   
        item_id = dynamodb_client.store_data(user_data)
        return jsonify({"message": "Data stored successfully", "id": item_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/fetch", methods=["GET"])
def retrieve_data():
    data = request.json
    if not data:
            return jsonify({"error": "Invalid input, JSON required"}), 400
    stored_data = dynamodb_client.fetch_data(data["id"])

    # Decrypt sensitive fields
    stored_data["mobile"] = dynamodb_client.decrypt_data(stored_data["mobile"])
    stored_data["aadhaar_number"] = dynamodb_client.decrypt_data(stored_data["aadhaar_number"])

    return jsonify(stored_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
