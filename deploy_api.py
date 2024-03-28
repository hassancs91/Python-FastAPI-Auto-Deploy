import socket
from ssh_connection import execute_command
import time
import streamlit as st


def test_folder_existence_and_create(ssh_client,target_folder):
    try:
        stdin, stdout, stderr = ssh_client.exec_command(f'if [ ! -d "{target_folder}" ]; then sudo mkdir -p {target_folder}; fi')
        stdout.channel.recv_exit_status()  # Wait for command to complete
        st.write(f"Folder {target_folder} checked and created if not exist.")
    except Exception as e:
        st.write(f"Error checking and creating folder: {e}")
        exit(1)

def test_domain_resolution(domain, ip):
    try:
        resolved_ip = socket.gethostbyname(domain)
        if resolved_ip == ip:
            st.write("Domain resolves to the correct IP.")
        else:
            st.write(f"Domain resolves to {resolved_ip}, but expected {ip}.")
            exit(1)
    except Exception as e:
        st.write(f"Error resolving domain: {e}")
        exit(1)

def install_dependencies(ssh_client):
    try:
        #wait_for_apt_lock_release(ssh_client, timeout=600)
        st.write("Installing dependencies (Python, Git, Nginx)...")
        dependencies = ['python3', 'python3-pip','python3-venv', 'git', 'nginx']
        execute_command(ssh_client, f'sudo apt-get update && sudo apt-get install -y {" ".join(dependencies)}')
        st.write("Dependencies installed.")
    except Exception as e:
        st.write(f"Error installing dependencies: {e}")
        exit(1)

def create_virtual_environment(ssh_client,target_folder):
    try:
        st.write("Creating a virtual environment...")
        execute_command(ssh_client, f'cd {target_folder} && python3 -m venv venv')
        st.write("Virtual environment created.")
    except Exception as e:
        st.write(f"Error creating virtual environment: {e}")
        exit(1)

def clone_repo(ssh_client,github_repo,github_token,target_folder,is_private_repo):
    try:
        st.write(f"Cloning repository {github_repo}...")

        repo_url = github_repo
        if is_private_repo:
            # Modify the URL to include the PAT for authentication
            repo_url = github_repo.replace('https://', f'https://{github_token}@')

        execute_command(ssh_client, f'sudo git clone {repo_url} {target_folder}')
        st.write("Repository cloned.")
        create_virtual_environment(ssh_client,target_folder)
    except Exception as e:
        st.write(f"Error cloning repository: {e}")
        exit(1)

def install_requirements(ssh_client,target_folder):
    try:
        st.write("Installing Python requirements silently...")
        # Activating the virtual environment and installing requirements silently
        execute_command(ssh_client, f'cd {target_folder} && source venv/bin/activate && pip install -q -r requirements.txt')
        st.write("Python requirements installed.")
    except Exception as e:
        st.write(f"Error installing Python requirements: {e}")
        exit(1)

def configure_nginx(ssh_client,nginx_config_name,domain_name):
    try:
        st.write("Configuring Nginx as a reverse proxy for FastAPI...")
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
        st.write("Nginx configured.")
    except Exception as e:
        st.write(f"Error configuring Nginx: {e}")
        exit(1)

def setup_service(ssh_client,service_name,vps_user,target_folder,exec_start_command):
    try:
        st.write("Setting up FastAPI as a systemd service...")
        service_file_path = f'/etc/systemd/system/{service_name}.service'
        service_file_content = f"""
        [Unit]
        Description=FastAPI Application
        After=network.target

        [Service]
        User={vps_user}
        WorkingDirectory={target_folder}
        ExecStart={exec_start_command}

        [Install]
        WantedBy=multi-user.target
        """
        execute_command(ssh_client, f'echo "{service_file_content}" | sudo tee {service_file_path}')
        execute_command(ssh_client, 'sudo systemctl daemon-reload')
        execute_command(ssh_client, f'sudo systemctl enable {service_name}')
        st.write("Systemd service for FastAPI setup complete.")
    except Exception as e:
        st.write(f"Error setting up FastAPI as a systemd service: {e}")
        exit(1)

def setup_ssl_silently(ssh_client,email_address,domain_name):
    try:
        #wait_for_apt_lock_release(ssh_client, timeout=600)
        st.write("Setting up SSL with Let's Encrypt...")
        #execute_command(ssh_client, 'sudo apt-get update')
        st.write("Installing certbot...")
        execute_command(ssh_client, 'sudo apt-get install -y certbot python3-certbot-nginx')
        # Ensure the command is non-interactive and agrees to terms, providing an email address
        st.write("Installing SSL Certificate...")
        execute_command(ssh_client, f'sudo certbot --nginx --non-interactive --agree-tos --email {email_address} -d {domain_name}')
        st.write("Configure autorenewal...")
        execute_command(ssh_client, 'sudo certbot renew --dry-run')
        st.write("SSL setup complete.")
    except Exception as e:
        st.write(f"Error setting up SSL: {e}")
        exit(1)

def check_service_status(ssh_client,service_name, retries=3, delay=5 ):
    try:
        st.write("Checking FastAPI service status...")

        for attempt in range(retries):
            st.write("Try Starting the service...")
            status_output = execute_command(ssh_client, f'sudo systemctl start {service_name}')
            st.write(f"start output: {status_output}")
            
            
            st.write("Checking if Active...")
            status_output = execute_command(ssh_client, f'sudo systemctl is-active {service_name}')
            st.write(f"is-active output: {status_output}")
            if "active" in status_output:
                st.write("FastAPI service is active and running.")
                return
            else:
                st.write(f"FastAPI service is not active. Attempt {attempt + 1} of {retries}. Retrying in {delay} seconds...")
                st.write("Try Starting the service...")
                status_output = execute_command(ssh_client, f'sudo systemctl start {service_name}')
                time.sleep(delay)

        st.write("Failed to start FastAPI service after multiple attempts.")
        exit(1)

    except Exception as e:
        st.write(f"Error checking FastAPI service status: {e}")
        exit(1)

def deploy_api(ssh_client, config):
    # Check if the domain resolves to the correct IP
    test_domain_resolution(config["domain_name"], config["vps_ip"])
    # Ensure the target folder exists or create it
    test_folder_existence_and_create(ssh_client,config["target_folder"])
    # Install necessary system dependencies
    install_dependencies(ssh_client)
    # Clone the repository from GitHub
    clone_repo(ssh_client,config["github_repo"],config["github_token"],config["target_folder"],config["is_private_repo"])
    # Install Python requirements from the requirements.txt file
    install_requirements(ssh_client,config["target_folder"])
    # Configure Nginx as a reverse proxy for FastAPI
    configure_nginx(ssh_client,config["nginx_config_name"],config["domain_name"])
    # Set up FastAPI as a systemd service
    setup_service(ssh_client,config["service_name"],config["vps_user"],config["target_folder"],config["exec_start_command"])
    # Set up SSL using Let's Encrypt
    setup_ssl_silently(ssh_client,config["email_address"],config["domain_name"])
