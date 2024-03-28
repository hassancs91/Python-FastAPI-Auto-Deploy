import streamlit as st
import config_manager as config_manager
from ssh_connection import test_ssh_connection, setup_ssh_client
from update_api import update_api_and_restart
from deploy_api import deploy_api, check_service_status


def establish_connection(vps_ip, vps_user, vps_password, ssh_key_file_path, ssh_key_passphrase, use_ssh_key):
    test_ssh_connection(vps_ip, vps_user,vps_password,use_ssh_key, key_file=ssh_key_file_path, key_passphrase=ssh_key_passphrase)
    return setup_ssh_client(vps_ip, vps_user,vps_password,use_ssh_key, key_file=ssh_key_file_path, key_passphrase=ssh_key_passphrase)


st.title("Python FastAPI Deployment Tool 🚀")

# Selectbox or sidebar for navigation
option = st.selectbox("Choose an Option:", ["Deploy API", "Update API" ,"Configure APIs"])

if option == "Configure APIs":
    config_manager.config_page()
elif option == "Deploy API":
    st.subheader("Deploy API")

    configs = config_manager.load_configs()
    config_name = st.selectbox("Choose Configuration", list(configs.keys()))

    if st.button("Deploy API"):
        with st.spinner(f"Deploying API..."):
            config = configs[config_name]
            # Setup SSH client
            ssh_client = establish_connection(config["vps_ip"],config["vps_user"],config["vps_password"],config["ssh_key_file_path"],config["ssh_key_passphrase"],config["use_ssh_key"])
            # Deploy or update based on selection
            deploy_api(ssh_client, config)

            # Check the status of the service after updating
            check_service_status(ssh_client,config["service_name"], retries=3, delay=5 )
            
            ssh_client.close()
            st.success(f"API Deployed successfully!")
        
elif option == "Update API":
    st.subheader("Update API")

    configs = config_manager.load_configs()
    config_name = st.selectbox("Choose Configuration", list(configs.keys()))

    if st.button("Update API"):
        with st.spinner(f"Updating API..."):
            config = configs[config_name]
            # Setup SSH client
            ssh_client = establish_connection(config["vps_ip"],config["vps_user"],config["vps_password"],config["ssh_key_file_path"],config["ssh_key_passphrase"],config["use_ssh_key"])
            #update the api
            update_api_and_restart(ssh_client,config["service_name"],config["target_folder"])
            # Check the status of the service after updating
            check_service_status(ssh_client,config["service_name"], retries=3, delay=5 )
            ssh_client.close()
            st.success(f"API Updated successfully!")
        

        

