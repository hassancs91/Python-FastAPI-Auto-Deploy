import paramiko

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

def test_ssh_connection(ip, username, password=None,use_ssh_key = False, key_file=None, key_passphrase=None):
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

def setup_ssh_client(ip, username, password=None, use_ssh_key = False, key_file=None, key_passphrase=None):
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