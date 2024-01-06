from flask import Flask, request, jsonify, send_file
import mysql.connector
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os, secrets
from flask_mail import Mail, Message
app = Flask(__name__)

# MySQL database connection setup
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="file_sharing"
)

cursor = db.cursor()

ALLOWED_EXTENSIONS = {'pptx', 'docx', 'xlsx'}

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sharma1227aditi@gmail.com'
app.config['MAIL_PASSWORD'] = 'kcun azvl vsne zmgn'
app.config['MAIL_DEFAULT_SENDER'] = ('Aditi Sharma', 'sharma1227aditi@gmail.com')

mail=Mail(app)
clients = []
uploaded_files=[]
# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for login
@app.route('/ops/login', methods=['POST'])
def ops_login():
    # Retrieve username and password from the request
    username = request.json.get('username')
    password = request.json.get('password')

    # Validate the credentials using the database
    cursor.execute("SELECT * FROM ops_user WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()

    if user:
        # If credentials are valid, return success
        return jsonify({"message": "Login Successful"}), 200
    else:
        # If credentials are not valid, return failure
        return jsonify({"error": "Invalid credentials"}), 401
    
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Check if the file is of allowed type
    if file and allowed_file(file.filename):
        ops_user = request.headers.get('X-Ops-User')  
        if ops_user:
            # Save the file securely
            filename = secure_filename(file.filename)
            file.save(os.path.join('uploads', filename))
            uploaded_files.append(filename)

            return jsonify({"message": "File uploaded successfully"}), 200
        else:
            return jsonify({"error": "Ops User authentication failed"}), 401
    else:
        return jsonify({"error": "Invalid file type"}), 400
    
@app.route('/signup', methods=['POST'])
def client_sign_up():
    
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if the email is unique 
    if any(client['email'] == email for client in clients):
        return jsonify({"error": "Email already exists"}), 400
    
    verification_token = secrets.token_urlsafe(32)

    # Create a dummy client user
    user = {"email": email, "password": password, "verification_token": verification_token}
    clients.append(user)

    # Generate an verification url
    verification_url = f"http://127.0.0.1:5000/verify?token={verification_token}"

    send_verification_email(email, verification_url)
    return jsonify({"message": "Client User Sign up successful", "verification_url": verification_url}), 201
    
def send_verification_email(email, verification_url):
    subject = 'Email Verification'
    body = f'Click on the following link to verify your email: {verification_url}'
    message = Message(subject, recipients=[email], body=body)
    mail.send(message)

@app.route('/verify', methods=['GET'])
def verify_user():
    verification_token = request.args.get('token')

    # Check if the token matches any user in the database
    for client in clients:
        if client.get('verification_token') == verification_token:
            # Remove the verification token as it's no longer needed
            del client['verification_token']
            return jsonify({"message": "Client User verification successful"}), 200

    return jsonify({"error": "Invalid verification token"}), 400


@app.route('/client/login', methods=['POST'])
def client_login():
    # Retrieve username and password from the request
    data=request.json
    print("Received data:", data)
    email = data.get('email')
    password =data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if is_valid_client(email, password):
        return jsonify({"message": "Client User Login Successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

def is_valid_client(email, password):
    for client in clients:
        if client['email'] == email and client['password']==password:
            return True
    return False

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Check if the client is authenticated
    client_email = request.headers.get('X-Client-Email')
    if not client_email:
        return jsonify({"error": "Client user authentication failed"}), 401

    # Check if the file exists
    file_path = os.path.join('uploads', filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # Provide the file for download
    return send_file(file_path, as_attachment=True)

# Route for listing all uploaded files for a client user
@app.route('/client/files', methods=['GET'])
def list_uploaded_files():
    # Check if the client is authenticated
    client_email = request.headers.get('X-Client-Email')
    if not client_email:
        return jsonify({"error": "Client user authentication failed"}), 401

    # Get the current working directory
    current_directory = os.getcwd()

    # Print the current working directory for debugging
    print("Current Working Directory:", current_directory)

    # Construct the path to the 'uploads' folder
    uploads_folder_path = os.path.join(current_directory, 'uploads')

    # Print the 'uploads' folder path for debugging
    print("Uploads Folder Path:", uploads_folder_path)

    # Check if the 'uploads' folder exists
    if not os.path.exists(uploads_folder_path):
        return jsonify({"error": "Uploads folder not found"}), 404

    # Get all files in the 'uploads' folder
    files_in_uploads = [f for f in os.listdir(uploads_folder_path) if os.path.isfile(os.path.join(uploads_folder_path, f))]

    # Filter files based on client's email
    client_files = [file for file in files_in_uploads]

    return jsonify({"files": client_files})

if __name__ == '__main__':
    app.run(debug=True)