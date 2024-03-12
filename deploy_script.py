import paramiko
import socket
import time

# Configuration for VPS and GitHub repository
vps_ip = ""  # IP address of the VPS
vps_user = "root"
vps_password = ""  # VPS password for SSH login
target_folder = ""  # Target folder on VPS where the app will reside


# SSH key authentication configuration
use_ssh_key = False  # Flag to use SSH key authentication
ssh_key_file_path = "/path/to/ssh/key"  # Path to SSH key file
ssh_key_passphrase = None  # Passphrase for SSH key (if applicable)


# GitHub repository configuration
github_repo = "https://github.com/hassancs91/SimplerDictionary-API.git"  # GitHub repository URL
is_private_repo = False  # Flag to indicate if the GitHub repository is private
github_token = "XXX"  # GitHub token for cloning private repository

# SSL configuration
domain_name = ""  # Domain name for the FastAPI app
email_address = ""  # Email for SSL setup with Let's Encrypt


update_api = False  # Flag to update the API instead of a fresh setup

# Service and Nginx configurations
service_name = "fastapi_app"  # Name of the systemd service
nginx_config_name = "fastapi_app"  # Name of the Nginx configuration file

# Command to start the FastAPI app
exec_start_command = f"{target_folder}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"


def execute_command(ssh_client, command):
    """
    Execute a command on the SSH server and wait for it to complete.
    Returns the command output.
    """
    stdin, stdout, stderr = ssh_client.exec_command(command)
    # Wait for the command to complete
    while not stdout.channel.exit_status_ready():
        # You can also check for timeouts or add sleep intervals here if needed
        pass

    exit_status = stdout.channel.recv_exit_status()  # Retrieves the exit status

    if exit_status != 0:
        print(f"Command '{command}' failed with exit status {exit_status}")
        print(stderr.read().decode())
        exit(1)

    return stdout.read().decode()

def test_ssh_connection(ip, username, password=None, key_file=None, key_passphrase=None):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if use_ssh_key:
            # Using key authentication
            key = paramiko.RSAKey.from_private_key_file(key_file, password=key_passphrase)
            client.connect(ip, username=username, pkey=key)
        else:
            # Using password authentication
            client.connect(ip, username=username, password=password)

        print("Successfully authenticated with the VPS.")
        client.close()
    except Exception as e:
        print(f"Failed to authenticate with the VPS: {e}")
        exit(1)

def test_folder_existence_and_create(ssh_client):
    try:
        stdin, stdout, stderr = ssh_client.exec_command(f'if [ ! -d "{target_folder}" ]; then sudo mkdir -p {target_folder}; fi')
        stdout.channel.recv_exit_status()  # Wait for command to complete
        print(f"Folder {target_folder} checked and created if not exist.")
    except Exception as e:
        print(f"Error checking and creating folder: {e}")
        exit(1)

def test_domain_resolution(domain, ip):
    try:
        resolved_ip = socket.gethostbyname(domain)
        if resolved_ip == ip:
            print("Domain resolves to the correct IP.")
        else:
            print(f"Domain resolves to {resolved_ip}, but expected {ip}.")
            exit(1)
    except Exception as e:
        print(f"Error resolving domain: {e}")
        exit(1)

def setup_ssh_client(ip, username, password=None, key_file=None, key_passphrase=None):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if use_ssh_key:
            # Using key authentication
            key = paramiko.RSAKey.from_private_key_file(key_file, password=key_passphrase)
            client.connect(ip, username=username, pkey=key)
        else:
            # Using password authentication
            client.connect(ip, username=username, password=password)

        return client
    except Exception as e:
        print(f"Error setting up SSH client: {e}")
        exit(1)

def install_dependencies(ssh_client):
    try:
        #wait_for_apt_lock_release(ssh_client, timeout=600)
        print("Installing dependencies (Python, Git, Nginx)...")
        dependencies = ['python3', 'python3-pip','python3-venv', 'git', 'nginx']
        execute_command(ssh_client, f'sudo apt-get update && sudo apt-get install -y {" ".join(dependencies)}')
        print("Dependencies installed.")
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        exit(1)

def create_virtual_environment(ssh_client):
    try:
        print("Creating a virtual environment...")
        execute_command(ssh_client, f'cd {target_folder} && python3 -m venv venv')
        print("Virtual environment created.")
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        exit(1)

def clone_repo(ssh_client):
    try:
        print(f"Cloning repository {github_repo}...")

        repo_url = github_repo
        if is_private_repo:
            # Modify the URL to include the PAT for authentication
            repo_url = github_repo.replace('https://', f'https://{github_token}@')

        execute_command(ssh_client, f'sudo git clone {repo_url} {target_folder}')
        print("Repository cloned.")
        create_virtual_environment(ssh_client)
    except Exception as e:
        print(f"Error cloning repository: {e}")
        exit(1)

def install_requirements(ssh_client):
    try:
        print("Installing Python requirements silently...")
        # Activating the virtual environment and installing requirements silently
        execute_command(ssh_client, f'cd {target_folder} && source venv/bin/activate && pip install -q -r requirements.txt')
        print("Python requirements installed.")
    except Exception as e:
        print(f"Error installing Python requirements: {e}")
        exit(1)

def configure_nginx(ssh_client):
    try:
        print("Configuring Nginx as a reverse proxy for FastAPI...")
        nginx_config_file = f"/etc/nginx/sites-available/{nginx_config_name}"
        nginx_config = (
            f"server {{\n"
            f"    listen 80;\n"
            f"    server_name {domain_name};\n\n"
            f"    location / {{\n"
            f"        proxy_pass http://localhost:8000;\n"
            f"        proxy_set_header Host \\$host;\n"
            f"        proxy_set_header X-Real-IP \\$remote_addr;\n"
            f"        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;\n"
            f"        proxy_set_header X-Forwarded-Proto \\$scheme;\n"
            f"    }}\n"
            f"}}\n"
        )
        execute_command(ssh_client, f'echo "{nginx_config}" | sudo tee {nginx_config_file}')
        execute_command(ssh_client, f'sudo ln -s {nginx_config_file} /etc/nginx/sites-enabled/')
        execute_command(ssh_client, 'sudo nginx -t && sudo systemctl restart nginx')
        print("Nginx configured.")
    except Exception as e:
        print(f"Error configuring Nginx: {e}")
        exit(1)

def setup_service(ssh_client):
    try:
        print("Setting up FastAPI as a systemd service...")
        service_file_path = f'/etc/systemd/system/{service_name}.service'
        service_file_content = f"""
        [Unit]
        Description=FastAPI Application
        After=network.target

        [Service]
        User={vps_user}
        WorkingDirectory={target_folder}
        ExecStart={exec_start_command.format(target_folder=target_folder)}

        [Install]
        WantedBy=multi-user.target
        """
        execute_command(ssh_client, f'echo "{service_file_content}" | sudo tee {service_file_path}')
        execute_command(ssh_client, 'sudo systemctl daemon-reload')
        execute_command(ssh_client, f'sudo systemctl enable {service_name}')
        print("Systemd service for FastAPI setup complete.")
    except Exception as e:
        print(f"Error setting up FastAPI as a systemd service: {e}")
        exit(1)

def setup_ssl_silently(ssh_client):
    try:
        #wait_for_apt_lock_release(ssh_client, timeout=600)
        print("Setting up SSL with Let's Encrypt...")
        execute_command(ssh_client, 'sudo apt-get update')
        execute_command(ssh_client, 'sudo apt-get install -y certbot python3-certbot-nginx')
        # Ensure the command is non-interactive and agrees to terms, providing an email address
        execute_command(ssh_client, f'sudo certbot --nginx --non-interactive --agree-tos --email {email_address} -d {domain_name}')
        execute_command(ssh_client, 'sudo certbot renew --dry-run')
        print("SSL setup complete.")
    except Exception as e:
        print(f"Error setting up SSL: {e}")
        exit(1)

def check_service_status(ssh_client, retries=3, delay=5):
    try:
        print("Checking FastAPI service status...")

        for attempt in range(retries):
            status_output = execute_command(ssh_client, f'sudo systemctl is-active {service_name}')

            if "active" in status_output:
                print("FastAPI service is active and running.")
                return
            else:
                print(f"FastAPI service is not active. Attempt {attempt + 1} of {retries}. Retrying in {delay} seconds...")
                time.sleep(delay)

        print("Failed to start FastAPI service after multiple attempts.")
        exit(1)

    except Exception as e:
        print(f"Error checking FastAPI service status: {e}")
        exit(1)
    
def force_update_application_and_restart_service(ssh_client):
    try:
        print("Forcing update of application from GitHub repository...")
        # Resetting any changes and pulling the latest code from the repository
        execute_command(ssh_client, f'cd {target_folder} && sudo git fetch --all')
        execute_command(ssh_client, f'cd {target_folder} && sudo git reset --hard origin/main')

        # Installing any new requirements
        print("Installing any new requirements...")
        execute_command(ssh_client, f'cd {target_folder} && source venv/bin/activate && pip install -r requirements.txt')

        # Restarting the FastAPI service
        print("Restarting the FastAPI service...")
        execute_command(ssh_client, f'sudo systemctl restart {service_name}')

        print("Forced application update and restart complete.")
    except Exception as e:
        print(f"Error in forced update of application and restarting service: {e}")
        exit(1)

def main():
    # Establish SSH connection to the VPS
    if use_ssh_key:
        # Test SSH connection using an SSH key
        test_ssh_connection(vps_ip, vps_user, key_file=ssh_key_file_path, key_passphrase=ssh_key_passphrase)
        # Set up SSH client using the SSH key
        ssh_client = setup_ssh_client(vps_ip, vps_user, key_file=ssh_key_file_path, key_passphrase=ssh_key_passphrase)
    else:
        # Test SSH connection using a password
        test_ssh_connection(vps_ip, vps_user, vps_password)
        # Set up SSH client using a password
        ssh_client = setup_ssh_client(vps_ip, vps_user, vps_password)

    if update_api:
        # If updating the API, run the update process
        force_update_application_and_restart_service(ssh_client)
        # Check the status of the service after updating
        check_service_status(ssh_client)
        # Close SSH connection
        ssh_client.close()
        print("FastAPI application update complete.")
    else:
        # If setting up a new deployment
        # Check if the domain resolves to the correct IP
        #test_domain_resolution(domain_name, vps_ip)
        # Ensure the target folder exists or create it
        test_folder_existence_and_create(ssh_client)
        # Install necessary system dependencies
        #install_dependencies(ssh_client)
        # Clone the repository from GitHub
        clone_repo(ssh_client)
        # Install Python requirements from the requirements.txt file
        install_requirements(ssh_client)
        # Configure Nginx as a reverse proxy for FastAPI
        configure_nginx(ssh_client)
        # Set up FastAPI as a systemd service
        setup_service(ssh_client)
        # Set up SSL using Let's Encrypt
        setup_ssl_silently(ssh_client)
        # Check if the FastAPI service is running correctly
        check_service_status(ssh_client)
        # Close SSH connection
        ssh_client.close()
        print("FastAPI application deployment complete.")

if __name__ == "__main__":
    main()
