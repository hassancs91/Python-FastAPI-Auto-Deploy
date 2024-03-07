import paramiko
import socket


# Replace these variables with your actual credentials and paths
vps_user = "root"
vps_password = "XXX"  # If you're using password authentication
github_repo = "https://github.com/hassancs91/test-fastapi.git"
target_folder = "/var/test/api1"
domain_name = "hsuperapi.com"
email_address = "hasan.70821@gmail.com"

# New configurations
service_name = "fastapi_app"  # Default service name
nginx_config_name = "fastapi"  # Default Nginx config name
enable_ssl = True  # Set to False to disable SSL setup

use_ssh_key = False  # Set to True to use SSH key authentication
ssh_key_file_path = "/path/to/ssh/key"  # Replace with the actual path to the SSH key
ssh_key_passphrase = None 

vps_ip = "146.190.117.68"



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
        print("Installing dependencies (Python, Git, Nginx)...")
        dependencies = ['python3', 'python3-pip','python3.11-venv', 'git', 'nginx']
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
        execute_command(ssh_client, f'sudo git clone {github_repo} {target_folder}')
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
        ExecStart={target_folder}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

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


def check_service_status(ssh_client):
    try:
        print("Checking FastAPI service status...")
        execute_command(ssh_client, 'sudo systemctl start fastapi-app')
        execute_command(ssh_client, 'sudo systemctl status fastapi-app')
        print("FastAPI service is active and running.")
    except Exception as e:
        print(f"Error checking FastAPI service status: {e}")
        exit(1)

    

def main():
    test_ssh_connection(vps_ip, vps_user, vps_password)


    if use_ssh_key:
        test_ssh_connection(vps_ip, vps_user, key_file=ssh_key_file_path, key_passphrase=ssh_key_passphrase)
        ssh_client = setup_ssh_client(vps_ip, vps_user, key_file=ssh_key_file_path, key_passphrase=ssh_key_passphrase)
    else:
        test_ssh_connection(vps_ip, vps_user, vps_password)
        ssh_client = setup_ssh_client(vps_ip, vps_user, vps_password)
    

    if enable_ssl:
        test_domain_resolution(domain_name, vps_ip)



    test_folder_existence_and_create(ssh_client)

    install_dependencies(ssh_client)
    clone_repo(ssh_client)
    install_requirements(ssh_client)
    configure_nginx(ssh_client)
    setup_service(ssh_client)


    if enable_ssl:
        setup_ssl_silently(ssh_client)


    check_service_status(ssh_client)

    ssh_client.close()
    print("FastAPI application deployment complete.")

if __name__ == "__main__":
    main()
