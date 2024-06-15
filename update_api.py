from ssh_connection import execute_command
import streamlit as st

def update_api_and_restart(ssh_client, github_token, service_name, target_folder, repo_url):
    try:
        st.write("Forcing update of application from GitHub repository...")

        # Construct the new repository URL with the token
        #new_repo_url = f"https://{github_token}@{repo_url}"
        new_repo_url = repo_url.replace('https://', f'https://{github_token}@')
        # Change the remote URL to the new one with the updated token
        execute_command(ssh_client, f'cd {target_folder} && sudo git remote set-url origin {new_repo_url}')

        # Fetching all branches and resetting to the latest commit on the main branch
        execute_command(ssh_client, f'cd {target_folder} && sudo git fetch --all')
        execute_command(ssh_client, f'cd {target_folder} && sudo git reset --hard origin/main')

        # Installing any new requirements
        st.write("Installing any new requirements...")
        execute_command(ssh_client, f'cd {target_folder} && source venv/bin/activate && pip install -r requirements.txt')

        # Restarting the FastAPI service
        st.write("Restarting the FastAPI service...")
        execute_command(ssh_client, f'sudo systemctl restart {service_name}')

        st.write("Forced application update and restart complete.")
    except Exception as e:
        st.write(f"Error in forced update of application and restarting service: {e}")
        exit(1)