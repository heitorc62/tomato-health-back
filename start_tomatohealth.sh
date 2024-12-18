#!/bin/bash

# Create .env file:
python init_env.py

# Load variables from the .env file
source .env

# Start only the Label Studio service
echo "Starting only the Label Studio service..."
docker compose up --build -d label-studio

# Wait for Label Studio to become healthy
echo "Waiting for Label Studio to be healthy..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose ps -q label-studio))" == "healthy" ]; do
  echo "Label Studio is not yet healthy. Checking again in 5 seconds..."
  sleep 5
done

echo "Label Studio is healthy."

# Retrieve the API token from Label Studio
echo "Retrieving Label Studio API token..."
API_KEY=$(docker compose exec -T label-studio label-studio user --username "$LABEL_STUDIO_USERNAME" | grep -oP "(?<='token': ')[a-f0-9]+")

# Check if the API_KEY was retrieved successfully
if [ -z "$API_KEY" ]; then
  echo "Error: Failed to retrieve API token from Label Studio"
  exit 1
fi

echo "API key retrieved: $API_KEY"

# Export the token to an environment file
# Check if LABEL_STUDIO_API_KEY exists in .env
if grep -q "^export LABEL_STUDIO_API_KEY=" .env; then
  # If it exists, update the value
  echo "The Label Studio API Key is present in the .env file. Updating it..."
  sed -i "s/^export LABEL_STUDIO_API_KEY=.*/export LABEL_STUDIO_API_KEY=$API_KEY/" .env
else
  # If it doesn't exist, add it to the end of the file
  echo "The Label Studio API Key is not present in the .env file. Appending it to the file..."
  echo "export LABEL_STUDIO_API_KEY=$API_KEY" >> .env
fi

# Start the remaining services using the updated .env file
echo "Starting remaining services with Docker Compose..."
docker compose down

# Load variables from the .env file
source .env
echo "API key set: $LABEL_STUDIO_API_KEY"

docker compose --env-file .env up --build    # Use --detach to run in the background

#echo "All services started with Label Studio API token set."

# Run script to upload dataset to S3 (checks are already made in the script)
#pip install boto3
#python upload_dataset_to_s3.py --bucket-name $S3_BUCKET --dataset-path ../Detector/datasets/plantdoc-Tomato-YOLO --endpoint http://localhost:9000 --access_key minioadmin --secret_access_key minioadmin