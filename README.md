
# TomatoHealth: Tomato Disease Detection Dataset Builder

**TomatoHealth** is a robust and reliable machine learning platform designed to create an advanced object detection dataset for identifying diseases in tomato leaves. This project combines a Flask-based back-end, a Next.js front-end, and an administrative CLI tool to automate and streamline the dataset creation and model training process. The end goal is to build a highly accurate YOLOv8 model for detecting various diseases in tomato plants.

## Project Overview

1. **Front-End User Interface**: The Next.js client interface allows users to upload images of tomato leaves to the Flask API.
2. **Back-End Processing (Flask)**: The Flask API is pre-equipped with a YOLOv8n model trained on an initial dataset. When a user uploads an image, the model detects and returns the diseases found in the image. Additionally, all uploaded images are stored in MinIO (for local development) as part of the dataset-building process.
3. **Admin Controls**: An admin CLI tool invites reviewers to join the platform via SendGrid. Reviewers can then verify model annotations, enhancing dataset quality. Once annotations are approved, they can be integrated into the dataset for retraining the YOLOv8 model.

## Key Features

- **Object Detection Model**: A YOLOv8n model pre-trained on an initial dataset for detecting tomato leaf diseases.
- **Dataset Management**: Images are stored in MinIO (locally, to decouple from AWS) for continued dataset expansion.
- **Reviewer Invitations**: Admins can invite reviewers through the CLI, requiring SendGrid API configuration.
- **Annotation Review**: Reviewers assess model annotations, improving data quality for subsequent training cycles.

---

## Requirements

- **Docker**: Ensures easy setup of dependencies and services.
- **Python 3.8+**: Required to run the CLI tool and for certain back-end components.
- **Ngrok**: Used for local development to expose endpoints.

## Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tomatohealth.git
cd tomatohealth
```

### 2. Configuration

Configure your environment settings in the `config.yaml` file. This file is essential for defining SendGrid settings and other parameters for the project.

```yaml
# config.yaml

# SendGrid API configuration
sendgrid_api_key: "YOUR_SENDGRID_API_KEY"
email_sender: "YOUR_SENDER_EMAIL@example.com"
```

> **Note:** Ensure that the SendGrid API key and sender email are valid. SendGrid is used to send invitation emails to reviewers.

### 3. Running the Project

After configuring `config.yaml`, you can start the project by running:

```bash
./start_tomatohealth.sh
```

This script will handle all setup, including checking for ngrok and starting necessary Docker services.

### 4. Using the Admin CLI

- **Invite Reviewers**: The admin CLI tool allows inviting reviewers to the platform. Invited reviewers will receive an email (via SendGrid) with a registration link.
- **Integrate Annotations**: After reviewers approve or adjust the model’s annotations, the admin can integrate these updated images into the dataset. The CLI tool allows admins to manage this process seamlessly.

---

## How to Use the Project

1. **Upload Images**: Users upload images via the Next.js front-end. Each image is sent to the Flask API, where the model detects and returns disease annotations.
2. **Review Annotations**: Invited reviewers can log in to the platform to review and validate model-generated annotations.
3. **Expand Dataset**: After annotation reviews, admins integrate the reviewed images into the dataset. This iterative process strengthens the model’s accuracy.

### Running with Docker Compose

The project is Dockerized for ease of use. After cloning the repository and configuring `config.yaml`, running `start_tomatohealth.sh` will start all required services in Docker.

### Automatic Ngrok Download

The `start_tomatohealth.sh` script will check for ngrok’s presence. If not installed, it downloads and sets up a fixed version to prevent compatibility issues.

---

## Folder Structure

```plaintext
tomatohealth/
├── frontend/                 # Next.js front-end code
├── backend/                  # Flask API and YOLOv8 model code
|   ├── admin/                # Admin CLI code for managing invitations and annotations
├── config.yaml               # Project configuration file
├── start_tomatohealth.sh     # Main script to start the application
└── README.md                 # Project documentation
```

## Additional Notes

- The dataset is stored in MinIO during local development to keep it decoupled from any AWS dependencies.
- The back-end model is pre-trained with a YOLOv8n architecture for rapid object detection tasks.
- `sendgrid_api_key` and `email_sender` are required for sending invitations to reviewers.

## License

This project is licensed under the MIT License.

---

With this setup, you’re ready to create, expand, and refine a high-quality dataset for tomato disease detection! Enjoy building and training with **TomatoHealth**!