import torch, socket, httpx, os, boto3
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, current_app
from flask_migrate import Migrate
from app.config.config import Config
from flask_jwt_extended import JWTManager
from label_studio_sdk.client import LabelStudio
from flask_login import LoginManager
from botocore.exceptions import ClientError

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def check_and_create_bucket():
    # Configurar cliente S3
    print(f"Endpoint: {os.getenv('AWS_S3_ENDPOINT')}")
    print(f"Access key: {os.getenv('AWS_ACCESS_KEY_ID')}")
    print(f"Secret key: {os.getenv('AWS_SECRET_ACCESS_KEY')}")
    print(f"Bucket: {os.getenv('S3_BUCKET')}")
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('AWS_S3_ENDPOINT'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    bucket_name = os.getenv('S3_BUCKET')
    
    try:
        # Tenta obter o bucket para verificar se ele existe
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' já existe.")
    except ClientError as e:
        # Se o erro indicar que o bucket não existe, cria-o
        if e.response['Error']['Code'] == '404':
            print(f"Bucket '{bucket_name}' não encontrado. Criando bucket...")
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' criado com sucesso.")
        else:
            print("Erro ao verificar o bucket:", e)
            raise

def get_label_studio_client():
    """Returns a Label Studio client instance."""
    try:
        # Create the client instance
        print(f"THE API KEY WE ARE USING IS: {current_app.config['LABEL_STUDIO_API_KEY']}")
        client = LabelStudio(
            base_url=current_app.config['LABEL_STUDIO_URL'],
            api_key=current_app.config['LABEL_STUDIO_API_KEY']
        )

        # Test the connection by listing the projects (or another lightweight request)
        client.projects.list()

        print("Label Studio client created successfully")
        return client
    except httpx.HTTPStatusError as e:
        # Log the status code and response body for further diagnosis
        print(f"Failed to create Label Studio client: HTTP error occurred: {e.response.status_code}")
        print(f"Response content: {e.response.text}")
    except httpx.RequestError as e:
        print(f"Failed to create Label Studio client: Request error occurred: {e}")
        print(f"Response content: {e.response.text}")
    except Exception as e:
        print(f"Failed to create Label Studio client: Unexpected error: {e}")
        print(f"Response content: {e.response.text}")


    return None
def create_project_if_not_exists(project_title='Image Review Project', client=None):
    """Checks if the Label Studio project exists, and creates it if it doesn't."""
    response = client.projects.list()
    for item in response:
        if item.title == project_title:
            return item.id
    # Create the project if it doesn't exist
    label_config =  '''
                        <View>
                        <Image name="image" value="$image"/>
                        <RectangleLabels name="label" toName="image">
                            <Label value="Tomato Early blight leaf"/>
                            <Label value="Tomato leaf"/>
                            <Label value="Tomato leaf bacterial spot"/>
                            <Label value="Tomato leaf late blight"/>
                            <Label value="Tomato leaf mosaic virus"/>
                            <Label value="Tomato leaf yellow virus"/>
                            <Label value="Tomato mold leaf"/>
                            <Label value="Tomato Septoria leaf spot"/>
                            <Label value="Tomato two spotted spider mites leaf"/>
                        </RectangleLabels>
                        </View>
                    '''
    project = client.projects.create(
        title=project_title,
        description='Tomato leaf disease detection project',
        label_config=label_config,
        expert_instruction='Please label the type of tomato leaf disease in the image',
    )    
    return project.id


def update_webhook(client, project_id):
    webhook_list= client.webhooks.list(project=project_id)
    if len(webhook_list) > 0:
        webhook_id = webhook_list[0].id
        client.webhooks.delete(id=webhook_id)
    
    client.webhooks.create(url=f"http://{socket.gethostbyname(socket.gethostname())}:5000/labelling_tool/webhook", project=project_id)
    

def create_app(config='app.config.config.Config'):
    app = Flask(__name__, template_folder='view')
    app.config.from_object(config)
    Config.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'Routes.login'  # Redirect here if not logged in

    # Load user callback for Flask-Login
    from app.models import ReviewerModel

    @login_manager.user_loader
    def load_user(user_id):
        return ReviewerModel.query.get(int(user_id))
    
    
    from app.models import load_models
    # Load the device and models after the app is configured
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    app.device = device
    app.models = load_models(app.config, device)
    
    # Initialize OpenAI API key
    app.openai_client = OpenAI()
    
    with app.app_context():
        try:
            app.label_studio_client = get_label_studio_client()
            app.LABEL_STUDIO_PROJECT_ID = create_project_if_not_exists('Image Review Project', app.label_studio_client)
            update_webhook(app.label_studio_client, app.LABEL_STUDIO_PROJECT_ID)
        except Exception as e:
            raise RuntimeError(f"Error during Label Studio project creation: {str(e)}")
        
        check_and_create_bucket()
    
    from app.controllers import routes_bp
    app.register_blueprint(routes_bp)
    
    return app




