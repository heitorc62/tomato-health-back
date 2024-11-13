import requests, sys, paramiko, os, subprocess, time
from dotenv import load_dotenv

# Define the base URL for the API
BASE_URL = "http://localhost:5000"

# Load environment variables from the .env file
load_dotenv()

# Store JWT token globally after login
jwt_token = None


def start_ngrok():
    """
    Starts all ngrok tunnels defined in the ngrok configuration file
    and retrieves their public URLs.
    """
    # Start ngrok with all defined tunnels in the configuration file
    ngrok_process = subprocess.Popen(['ngrok', 'start', '--all'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)  # Give ngrok some time to initialize

    try:
        # Retrieve URLs for all tunnels
        response = requests.get("http://localhost:4040/api/tunnels")
        response.raise_for_status()
        tunnels = response.json()['tunnels']

        # Collect URLs for each tunnel
        urls = {tunnel['name']: tunnel['public_url'] for tunnel in tunnels}
        for name, url in urls.items():
            print(f"Ngrok tunnel '{name}' created at {url}")

        return urls

    except Exception as e:
        stdout, stderr = ngrok_process.communicate()
        print(f"Failed to retrieve ngrok URLs: {str(e)}")
        print("Ngrok stdout:", stdout.decode())
        print("Ngrok stderr:", stderr.decode())
        ngrok_process.terminate()
        return None


def register_admin():
    """Registers a new admin user."""
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    # Send a POST request to the /admin_register endpoint
    response = requests.post(f"{BASE_URL}/register_admin", json={"username": username, "password": password})

    if response.status_code == 201:
        print("Admin user registered successfully.")
    else:
        print(f"Failed to register admin user. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def get_auth_headers():
    """Returns the authorization headers with JWT token."""
    global jwt_token
    if jwt_token:
        return {"Authorization": f"Bearer {jwt_token}"}
    return {}

def login_admin():
    """Handles admin login and retrieves the JWT token."""
    global jwt_token
    if jwt_token:
        print("You are already logged in.")
        return

    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    # Send a POST request to the /admin_login endpoint to get the JWT
    response = requests.post(f"{BASE_URL}/admin_login", json={"username": username, "password": password})

    if response.status_code == 200:
        jwt_token = response.json().get('access_token')
        print("Login successful. JWT token received.")
    else:
        print(f"Login failed. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def send_invitation():
    """Sends an invitation email to a reviewer using JWT token."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return

    email = input("Enter the reviewer's email address: ")

    # Send a POST request to the /invite_reviewer endpoint
    response = requests.post(f"{BASE_URL}/invite_reviewer", headers=get_auth_headers(), json={"email": email})

    if response.status_code == 201:
        print(f"Invitation sent to {email}.")
    else:
        print(f"Failed to send invitation. Status Code: {response.status_code}, Message: {response.json().get('msg')}")

def update_tomato_dataset():
    """Updates the tomato dataset with reviewed images using JWT token."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return
    try:
        response = requests.post(f"{BASE_URL}/update_dataset", headers=get_auth_headers())
    except Exception as e:
        print(f"Failed to update dataset: {str(e)}")
        return
    if response.status_code == 200:
        print(f"Tomato dataset updated successfully.\n{response.json()}")
    else:
        print(f"Failed to update dataset. Status Code: {response.status_code}, Message: {response.json().get('msg')}")
        
def retrain_model_remote_within_network(path_to_script, dataset_name, s3_access_key, s3_secret_key):
    # Retrieve SSH credentials from environment variables
    shell_host = os.getenv("SSH_HOST")  # e.g., 'shell.vision.ime.usp.br'
    shell_user = os.getenv("SSH_USER")  # e.g., 'heitorc62'
    shell_password = os.getenv("SSH_PASSWORD")  # Your password for the shell machine
    
    gpu_host = os.getenv('GPU_SSH_HOST')
    gpu_user = os.getenv("SSH_USER")  # e.g., 'heitorc62'
    gpu_password = os.getenv("SSH_PASSWORD")  # Your password for the deepthree machine
    
    
    if not shell_host or not shell_user or not shell_password:
        print("Missing first machine SSH credentials. Please check your .env file.")
        return

    if not gpu_user or not gpu_password:
        print("Missing second machine SSH credentials. Please check your .env file.")
        return
    
    # Start ngrok and retrieve the URLs
    urls = start_ngrok()
    if not urls:
        print("Failed to start ngrok tunnels. Aborting remote training.")
        return

    # Assign the URLs to respective variables based on ports
    ngrok_url = urls.get('primary_tunnel')
    s3_ngrok_url = urls.get('s3_tunnel')

    # Command to SSH into deepthree and run a script
    deepthree_command = f"ssh {gpu_host} 'bash {path_to_script} {dataset_name} {ngrok_url} {s3_ngrok_url} {s3_access_key} {s3_secret_key}'"

    try:
        # Create an SSH client for the shell machine
        shell_ssh = paramiko.SSHClient()
        shell_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the shell machine
        shell_ssh.connect(hostname=shell_host, username=shell_user, password=shell_password)
        
        print(f"Connected to {shell_host}.")

        # SSH into the deepthree machine from the shell machine and run the script
        deepthree_ssh_command = f"sshpass -p {gpu_password} {deepthree_command}"

        stdin, stdout, stderr = shell_ssh.exec_command(deepthree_ssh_command)
        
        # Optional: Retrieve command output/errors
        output = stdout.read().decode()
        errors = stderr.read().decode()

        if errors:
            print(f"Error during the second SSH to deepthree: {errors}")
        else:
            print(f"Training process started successfully on deepthree. Output:\n{output}")
        
        # Close the SSH connection to the shell machine
        shell_ssh.close()

    except Exception as e:
        print(f"Failed to execute the remote script: {str(e)}")
        
def retrain_model_remote(path_to_script, dataset_name, s3_access_key, s3_secret_key):
    """
    Directly SSH into the remote machine (deepthree) to run the training script from an external network.
    """
    gpu_host = os.getenv('GPU_SSH_HOST')
    gpu_user = os.getenv("GPU_SSH_USER")
    gpu_password = os.getenv("GPU_SSH_PASSWORD")

    if not gpu_host or not gpu_user or not gpu_password:
        print("Missing remote SSH credentials. Please check your .env file.")
        return
    
    # Start ngrok and retrieve the URLs
    urls = start_ngrok()
    if not urls:
        print("Failed to start ngrok tunnels. Aborting remote training.")
        return

    # Assign the URLs to respective variables based on ports
    ngrok_url = urls.get('primary_tunnel')
    s3_ngrok_url = urls.get('s3_tunnel')

    try:
        # Create an SSH client for the GPU machine
        gpu_ssh = paramiko.SSHClient()
        gpu_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect directly to the GPU machine
        gpu_ssh.connect(hostname=gpu_host, username=gpu_user, password=gpu_password)
        
        print(f"Connected to {gpu_host}.")

        # Command to run the training script on the GPU machine
        gpu_command = f"bash {path_to_script} {dataset_name} {ngrok_url} {s3_ngrok_url} {s3_access_key} {s3_secret_key}"
        stdin, stdout, stderr = gpu_ssh.exec_command(gpu_command)
        
        # Retrieve command output/errors
        output = stdout.read().decode()
        errors = stderr.read().decode()

        if errors:
            print(f"Error during training on {gpu_host}: {errors}")
        else:
            print(f"Training process started successfully on {gpu_host}. Output:\n{output}")
        
        gpu_ssh.close()

    except Exception as e:
        print(f"Failed to execute the remote script on {gpu_host}: {str(e)}")


def retrain_mode_local(path_to_script, dataset_name, s3_access_key, s3_secret_key):
    """
    Run the training script locally on the machine.
    """
    server_url = "http://localhost:5000"
    s3_url = "http://localhost:9000"
    try:
        # Run the training script locally
        result = os.system(f"bash {path_to_script} {dataset_name} {server_url} {s3_url} {s3_access_key} {s3_secret_key}")
        if result == 0:
            print("Local training process started successfully.")
        else:
            print("Failed to start local training process.")
    except Exception as e:
        print(f"Failed to execute the local training script: {str(e)}")
        
def retrain_model():
    path_to_script = input("Enter the path to the training script: ")
    dataset_name = input("Enter the name of the dataset: ")
    training_method = os.getenv('TRAINING_METHOD')
    s3_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    s3_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    print(f"Training method: {training_method}")
    print(f"Dataset name: {dataset_name}")
    print(f"S3 Access Key: {s3_access_key}")
    print(f"S3 Secret Key: {s3_secret_key}")
    if training_method == 'remote_within_network':
        retrain_model_remote_within_network(path_to_script, dataset_name, s3_access_key, s3_secret_key)
    elif training_method == 'remote':
        retrain_model_remote(path_to_script, dataset_name, s3_access_key, s3_secret_key)
    else:
        retrain_mode_local(path_to_script, dataset_name, s3_access_key, s3_secret_key)
    

def update_model():
    """Retrains the model by uploading new weights directly to the server using a POST request."""
    if not jwt_token:
        print("Please log in as an admin first.")
        return

    # Get the local file path for the model weights
    weights_file_path = input("Please enter the path to the model weights file: ")

    try:
        # Open the model weights file in binary mode
        with open(weights_file_path, 'rb') as weights_file:
            # Send the POST request with the file as multipart/form-data
            files = {'weights': weights_file}
            response = requests.post(f"{BASE_URL}/update_weights", files=files, headers=get_auth_headers())

        # Handle the response
        if response.status_code == 200:
            print("Model updated successfully with new weights.")
        else:
            print(f"Failed to update model. Status Code: {response.status_code}, Message: {response.json().get('error')}")
    except FileNotFoundError:
        print("The specified weights file was not found. Please check the file path and try again.")

def exit():
    """Exits the admin panel."""
    print("Exiting the admin panel. Goodbye!")
    sys.exit()