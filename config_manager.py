import streamlit as st
import json
import os

# File to store the configurations
CONFIG_FILE = "api_configs.json"

def load_configs():
    """Load existing configurations from a JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

def save_configs(configs):
    """Save configurations to a JSON file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(configs, file, indent=4)

def config_page():
    """Streamlit page for managing API configurations."""
    st.title("API Configuration Manager")

    configs = load_configs()

    # Dropdown to select a configuration
    config_names = list(configs.keys())
    selected_config = st.selectbox("Select a Configuration to Edit or Delete", [""] + config_names)

    if selected_config:
        config_data = configs[selected_config]
    else:
        config_data = {}
    # Load the selected configuration for editing
    #config_data = configs.get(selected_config, {}) if selected_config else {}

    with st.form("config_form"):
        st.subheader(f"{'Edit' if selected_config else 'Add'} API Configuration")

        # Fields for configuration
        name = st.text_input("Configuration Name", value=selected_config if selected_config else "", help="A unique name for this configuration")
        vps_ip = st.text_input("VPS IP",value=config_data.get("vps_ip", ""))
        vps_user = st.text_input("VPS User",value=config_data.get("vps_user", ""))
        vps_password = st.text_input("VPS Password", type="password",value=config_data.get("vps_password", ""))
        use_ssh_key = st.checkbox("Use SSH Key",value=config_data.get("use_ssh_key", False))


        # Conditional fields based on the state of 'use_ssh_key'
        ssh_key_file_path = ""
        ssh_key_passphrase = ""

        ssh_key_file_path = st.text_input("SSH Key Path (Optioanal if SSH Key Authentication)",value=config_data.get("ssh_key_file_path", ""))
        ssh_key_passphrase = st.text_area("SSH Key Passphrase (Optioanal if SSH Key Authentication )",value=config_data.get("ssh_key_passphrase", ""), help="Enter the passphrase for your SSH key, if any.")

        
        target_folder = st.text_input("Target Folder on Server",value=config_data.get("target_folder", ""))

        github_repo = st.text_input("GitHub Repository URL",value=config_data.get("github_repo", ""))
        is_private_repo = st.checkbox("Private Repository", value=config_data.get("is_private_repo", False))
        github_token = st.text_input("Github Token (Optional if Private Repository)",value=config_data.get("github_token", ""))


        domain_name = st.text_input("Domain Name",value=config_data.get("domain_name", ""))
        email_address = st.text_input("Email Address (Used By Let's Encrypt)",value=config_data.get("email_address", ""))

        service_name = st.text_input("Service Name",value=config_data.get("service_name", ""))
        nginx_config_name = st.text_input("Nginx Config Name",value=config_data.get("nginx_config_name", ""))

        # Construct exec_start_command
        default_exec_start_command = "/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2"
        exec_start_command = st.text_input("Service Execution Command",value=config_data.get("exec_start_command", default_exec_start_command))

        # Save or Update button
        submit_button = st.form_submit_button("Save Configuration")

    if submit_button:
        # Save the configuration (handle both add and edit)
        if selected_config and name != selected_config:
            # Handle the case where the name has been changed
            configs.pop(selected_config)
        configs[name] = {
            "vps_ip": vps_ip,
            "vps_user": vps_user,
            "vps_password": vps_password,
            "use_ssh_key": use_ssh_key,
            "ssh_key_file_path": ssh_key_file_path,
            "ssh_key_passphrase": ssh_key_passphrase,
            "target_folder": target_folder,
            "github_repo": github_repo,
            "is_private_repo": is_private_repo,
            "github_token": github_token,
            "domain_name": domain_name,
            "email_address": email_address,
            "service_name" : service_name,
            "nginx_config_name" : nginx_config_name,
            "exec_start_command": exec_start_command

        }
        save_configs(configs)
        st.success(f"Configuration '{name}' saved!")

    # Button to delete the selected configuration
    if selected_config and st.button("Delete Configuration"):
         st.session_state["to_delete"] = selected_config

    if "to_delete" in st.session_state and st.session_state["to_delete"] == selected_config:
        if st.button(f"Confirm Deletion of '{selected_config}'"):
            configs.pop(selected_config)
            save_configs(configs)
            st.success(f"Configuration '{selected_config}' deleted!")
            del st.session_state["to_delete"]

