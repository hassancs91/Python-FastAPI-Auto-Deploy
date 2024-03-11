# FastAPI Automated Deployment Script

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project contains a Python script for automating the deployment of FastAPI applications on an Ubuntu VPS. It simplifies the process of setting up a FastAPI server, including cloning from a GitHub repository, configuring Nginx as a reverse proxy, and setting up SSL with Let's Encrypt.

## Features

- Automates FastAPI deployment on Ubuntu VPS
- Supports both SSH key and password authentication
- Auto-configures Nginx and SSL
- Options for updating existing FastAPI applications

## Getting Started

To use this script, clone the repository and modify the configuration variables in the script to match your server and application details.

### Prerequisites

- A VPS running Ubuntu
- SSH access to the VPS
- A GitHub repository with your FastAPI application

### Usage

1. Clone this project to your local machine.
2. Open the script and fill in your VPS and GitHub repository details.
3. Run the script to deploy or update your FastAPI application.

## Configuration Variables

Before running the script, you will need to set several configuration variables. These variables are essential for the script to interact with your VPS and GitHub repository correctly. Below is a description of each variable and where you can find the necessary information.

### VPS Configuration

- `vps_user`: The username for SSH access to your VPS (usually `root`).
- `vps_password`: The password for SSH access if you are not using SSH key authentication.
- `vps_ip`: The IP address of your VPS.

### SSH Configuration

- `use_ssh_key`: Set to `True` if you are using SSH key authentication, otherwise `False`.
- `ssh_key_file_path`: The file path of your SSH private key, required if `use_ssh_key` is `True`.
- `ssh_key_passphrase`: The passphrase for your SSH key, if applicable.

### GitHub Repository Configuration

- `github_repo`: The URL of your FastAPI application's GitHub repository.
- `is_private_repo`: Set to `True` if your GitHub repository is private, otherwise `False`.
- `github_token`: Your GitHub access token, required if `is_private_repo` is `True`.

### Application and Domain Configuration

- `target_folder`: The target directory on your VPS where the FastAPI application will be stored.
- `domain_name`: The domain name that will point to your FastAPI application.
- `email_address`: The email address for SSL certificate registration with Let's Encrypt.

### Deployment Options

- `update_api`: Set to `True` if you want to update an existing application, otherwise `False`.
- `service_name`: The name of the systemd service for your FastAPI application.
- `nginx_config_name`: The name for your Nginx configuration file.

Ensure all these variables are correctly set in the script before executing it to ensure a smooth deployment process.


## Domain Setup

- Ensure that the DNS settings for your domain name (`domain_name`) are configured to point to your VPS IP address (`vps_ip`). This is necessary for your domain to correctly resolve to your FastAPI application.


## Planned Updates

- Adaptation to support Django and Flask frameworks.
- Expansion to allow deployment on multiple operating systems.
- Making SSL setup optional.
- Adding comprehensive logging for better debugging and monitoring.

## Contributing

Contributions are welcome! Feel free to submit a pull request or create an issue for any bugs, feature requests, or improvements.

## License

This project is licensed under the MIT License
