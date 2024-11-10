import os
import boto3
from argparse import ArgumentParser


def dataset_already_uploaded(s3_client, bucket_name, marker_key):
    # Check if the marker file exists in the bucket
    try:
        s3_client.head_object(Bucket=bucket_name, Key=marker_key)
        print("Dataset already uploaded.")
        return True
    except s3_client.exceptions.ClientError:
        # Marker file does not exist
        return False

def upload_dataset_to_s3(bucket_name, dataset_path, endpoint, access_key, secrect_access_key, marker_key="dataset_uploaded.marker"):
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secrect_access_key
    )

    # Check if dataset is already uploaded
    if dataset_already_uploaded(s3_client, bucket_name, marker_key):
        return  # Exit if dataset is already uploaded

    # Upload each file in the dataset directory
    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            file_path = os.path.join(root, file)
            s3_key = os.path.relpath(file_path, dataset_path)
            s3_key = os.path.join("dataset", s3_key)
            try:
                s3_client.upload_file(file_path, bucket_name, s3_key)
                print(f"Uploaded {file_path} to s3://{bucket_name}/dataset/{s3_key}")
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")

    # Create the marker file in S3 after successful upload
    s3_client.put_object(Bucket=bucket_name, Key=marker_key, Body="")

# Example usage
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--bucket_name", type=str, required=True)
    parser.add_argument("--dataset_path", type=str, required=True)
    parser.add_argument("--endpoint", type=str, required=True)
    parser.add_argument("--access_key", type=str, required=True)
    parser.add_argument("--secret_access_key", type=str, required=True)
    args = parser.parse_args()
    upload_dataset_to_s3(args.bucket_name, args.dataset_path, args.endpoint, args.access_key, args.secret_access_key)