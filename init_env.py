import yaml, secrets

# Load user-specific configurations from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Fixed environment variables
fixed_env_vars = [
    'export LABEL_STUDIO_URL=http://label-studio:8080',
    'export LABEL_STUDIO_USERNAME=admin@tomatohealth.com.br',
    'export LABEL_STUDIO_PASSWORD=tomatohealthpassword',
    'export DATABASE_URL=postgresql://tomato_user:123456@postgres/tomato_db',
    'export POSTGRES_DB=tomato_db',
    'export POSTGRES_USER=tomato_user',
    'export POSTGRES_PASSWORD=123456',
    'export POSTGRES_HOST=postgres',
    'export PGADMIN_DEFAULT_EMAIL=admin@example.com',
    'export PGADMIN_DEFAULT_PASSWORD=admin',
    'export AWS_REGION=sa-east-1',
    'export S3_BUCKET=tomato-dataset',
    'export S3_DATASET_PATH=dataset',
    'export S3_NEW_IMAGES_PATH=new_images',
    'export AWS_ACCESS_KEY_ID=minioadmin',
    'export AWS_SECRET_ACCESS_KEY=minioadmin',
    'export AWS_S3_ENDPOINT=http://minio:9000', # Endpoint para MinIO
    f'export SECRET={secrets.token_hex(32)}',
]

# User-specific environment variables from config.yaml
user_env_vars = [
    f"export SENDGRID_API_KEY={config['sendgrid']['api_key']}",
    f"export MAIL_DEFAULT_SENDER={config['sendgrid']['verified_sender']}",
    f"export OPENAI_API_KEY={config['openai']['api_key']}",
]

# Training method variables
training_method = config['training']['method']
user_env_vars.append(f"export TRAINING_METHOD={training_method}")

if training_method == 'remote':
    remote_ssh = config['training']['remote_ssh']
    user_env_vars.extend([
        f"export SSH_HOST={remote_ssh['host']}",
        f"export SSH_USER={remote_ssh['user']}",
        f"export SSH_AUTH_METHOD={remote_ssh['auth_method']}"
    ])
    if remote_ssh['auth_method'] == 'key':
        user_env_vars.append(f"export SSH_KEY_PATH={remote_ssh['key_path']}")
    elif remote_ssh['auth_method'] == 'password':
        user_env_vars.append(f"export SSH_PASSWORD={remote_ssh['password']}")
elif training_method == 'remote_within_network':
    # Remote SSH details
    remote_ssh = config['training']['remote_ssh']
    user_env_vars.extend([
        f"export SSH_HOST={remote_ssh['host']}",
        f"export SSH_USER={remote_ssh['user']}",
        f"export SSH_AUTH_METHOD={remote_ssh['auth_method']}"
    ])
    if remote_ssh['auth_method'] == 'key':
        user_env_vars.append(f"export SSH_KEY_PATH={remote_ssh['key_path']}")
    elif remote_ssh['auth_method'] == 'password':
        user_env_vars.append(f"export SSH_PASSWORD={remote_ssh['password']}")
    
    # Network SSH details
    network_ssh = config['training']['network_ssh']
    user_env_vars.extend([
        f"export GPU_SSH_HOST={network_ssh['host_within_network']}",
        f"export NETWORK_SSH_USER={network_ssh['user']}",
        f"export NETWORK_SSH_AUTH_METHOD={network_ssh['auth_method']}"
    ])
    if network_ssh['auth_method'] == 'key':
        user_env_vars.append(f"export NETWORK_SSH_KEY_PATH={network_ssh['key_path']}")
    elif network_ssh['auth_method'] == 'password':
        user_env_vars.append(f"export NETWORK_SSH_PASSWORD={network_ssh['password']}")

# Combine fixed and user-specific environment variables
all_env_vars = fixed_env_vars + user_env_vars

# Write to .env file
with open('.env', 'w') as env_file:
    for var in all_env_vars:
        env_file.write(var + '\n')
