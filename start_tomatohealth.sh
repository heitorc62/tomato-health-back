#!/bin/bash

# Step 0: Load variables from the .env file
export $(grep -v '^#' .env | xargs)

# Step 1: Start only the Label Studio service
echo "Starting only the Label Studio service..."
docker compose up --build -d label-studio

# Step 2: Wait for Label Studio to become healthy
echo "Waiting for Label Studio to be healthy..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose ps -q label-studio))" == "healthy" ]; do
  echo "Label Studio is not yet healthy. Checking again in 5 seconds..."
  sleep 5
done

echo "Label Studio is healthy."

# Step 3: Retrieve the API token from Label Studio
echo "Retrieving Label Studio API token..."
API_KEY=$(docker compose exec -T label-studio label-studio user --username "$LABEL_STUDIO_USERNAME" | grep -oP "(?<='token': ')[a-f0-9]+")

# Check if the API_KEY was retrieved successfully
if [ -z "$API_KEY" ]; then
  echo "Error: Failed to retrieve API token from Label Studio"
  exit 1
fi

echo "API key retrieved: $API_KEY"

# Step 4: Export the token to an environment file
echo "Setting LABEL_STUDIO_API_KEY in .env file for main services..."
sed -i "s/^export LABEL_STUDIO_API_KEY=.*/export LABEL_STUDIO_API_KEY=$API_KEY/" .env

# Step 5: Start the remaining services using the updated .env file
echo "Starting remaining services with Docker Compose..."
docker compose down

# Step 0: Load variables from the .env file
export $(grep -v '^#' .env | xargs)
echo "API key set: $LABEL_STUDIO_API_KEY"

docker compose --env-file .env up --build

#echo "All services started with Label Studio API token set."
