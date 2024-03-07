import paramiko
import socket


# Replace these variables with your actual credentials and paths
vps_ip = "146.190.117.68"
vps_user = "root"
vps_password = "3anka2lma8reB_api"  # If you're using password authentication
github_repo = "https://github.com/hassancs91/test-fastapi.git"
target_folder = "/var/test/api1"
domain_name = "hsuperapi.com"


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



def test_ssh_connection(ip, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password)
        print("Successfully authenticated with the VPS.")
        client.close()
    except Exception as e:
        print(f"Failed to authenticate with the VPS: {e}")
        exit(1)

def test_folder_existence(ssh_client):
    try:
        stdin, stdout, stderr = ssh_client.exec_command(f'if [ -d "{target_folder}" ]; then echo "Directory exists"; else echo "Directory does not exist"; fi')
        result = stdout.read().decode().strip()
        print(f"Folder check: {result}")
        if "does not exist" in result:
            exit(1)
    except Exception as e:
        print(f"Error checking folder existence: {e}")
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

def setup_ssh_client(ip, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password)
        return client
    except Exception as e:
        print(f"Error setting up SSH client: {e}")
        exit(1)

def install_dependencies(ssh_client):
    try:
        print("Installing dependencies (Python, Git, Nginx)...")
        dependencies = ['python3', 'python3-pip', 'git', 'nginx']
        execute_command(ssh_client, f'sudo apt-get update && sudo apt-get install -y {" ".join(dependencies)}')
        execute_command(ssh_client, f'sudo apt-get install uvicorn')
        print("Dependencies installed.")
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        exit(1)

def clone_repo(ssh_client):
    try:
        print(f"Cloning repository {github_repo}...")
        execute_command(ssh_client, f'sudo git clone {github_repo} {target_folder}')
        print("Repository cloned.")
    except Exception as e:
        print(f"Error cloning repository: {e}")
        exit(1)

def install_requirements(ssh_client):
    try:
        print("Installing Python requirements...")
        #execute_command(ssh_client, f'cd {target_folder} && sudo pip3 install -r requirements.txt')
        #execute_command(ssh_client, f'sudo apt install -r requirements.txt')
    
        print("Python requirements installed.")
    except Exception as e:
        print(f"Error installing Python requirements: {e}")
        exit(1)

def configure_nginx(ssh_client):
    try:
        print("Configuring Nginx as a reverse proxy for FastAPI...")
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
        execute_command(ssh_client, f'echo "{nginx_config}" | sudo tee /etc/nginx/sites-available/fastapi')
        execute_command(ssh_client, 'sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled')
        execute_command(ssh_client, 'sudo nginx -t && sudo systemctl restart nginx')
        print("Nginx configured.")
    except Exception as e:
        print(f"Error configuring Nginx: {e}")
        exit(1)

def setup_service(ssh_client):
    try:
        print("Setting up FastAPI as a systemd service...")
        service_file_content = f"""
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User={vps_user}
WorkingDirectory={target_folder}
ExecStart=/usr/bin/env uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
        """
        service_file_path = '/etc/systemd/system/fastapi-app.service'
        execute_command(ssh_client, f'echo "{service_file_content}" | sudo tee {service_file_path}')
        execute_command(ssh_client, 'sudo systemctl daemon-reload')
        execute_command(ssh_client, 'sudo systemctl enable fastapi-app')
        print("Systemd service for FastAPI setup complete.")
    except Exception as e:
        print(f"Error setting up FastAPI as a systemd service: {e}")
        exit(1)

def setup_ssl(ssh_client):
    try:
        print("Setting up SSL with Let's Encrypt...")
        execute_command(ssh_client, 'sudo apt-get update')
        execute_command(ssh_client, 'sudo apt-get install certbot python3-certbot-nginx')
        execute_command(ssh_client, f'sudo certbot --nginx -d {domain_name}')
        execute_command(ssh_client, 'sudo certbot renew --dry-run')
        print("SSL setup complete.")
    except Exception as e:
        print(f"Error setting up SSL: {e}")
        exit(1)

def main():
    test_ssh_connection(vps_ip, vps_user, vps_password)
    ssh_client = setup_ssh_client(vps_ip, vps_user, vps_password)
    test_folder_existence(ssh_client)
    test_domain_resolution(domain_name, vps_ip)

    install_dependencies(ssh_client)
    clone_repo(ssh_client)
    install_requirements(ssh_client)
    configure_nginx(ssh_client)
    setup_service(ssh_client)
    setup_ssl(ssh_client)
    ssh_client.close()
    print("FastAPI application deployment complete.")

if __name__ == "__main__":
    main()
