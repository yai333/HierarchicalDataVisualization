import pytest
import boto3
import os
from moto import mock_s3


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "11ttt11"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "te2222ting"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"
    os.environ["STAGE"] = "dev"
    os.environ["S3_BUCKET"] = "aiyi.data.visualization"


@pytest.fixture
def s3_client(aws_credentials):
    with mock_s3():
        s3 = boto3.client('s3')
        yield s3


@pytest.fixture
def create_bucket(s3_client):
    s3_client.create_bucket(Bucket=os.environ["S3_BUCKET"])


@pytest.fixture
def upload_default_csv(s3_client):
    s3_client.upload_file(
        'documents/default.csv', os.environ["S3_BUCKET"], 'dev/uploads/emp.csv')


@pytest.fixture
def upload_two_levels_csv(s3_client):
    s3_client.upload_file(
        'documents/two_levels.csv', os.environ["S3_BUCKET"], 'dev/uploads/two_levels.csv')


@pytest.fixture
def upload_three_levels_csv(s3_client):
    s3_client.upload_file(
        'documents/three_levels.csv', os.environ["S3_BUCKET"], 'dev/uploads/three_levels.csv')


@pytest.fixture
def upload_two_levels_emp_no_manager(s3_client):
    s3_client.upload_file(
        'documents/one_level_emp_no_manager.csv', os.environ["S3_BUCKET"],
        'dev/uploads/two_levels_emp_no_manager.csv')


@pytest.fixture
def upload_default_emp_with_noid(s3_client):
    s3_client.upload_file(
        'documents/default_emp_with_noid.csv', os.environ["S3_BUCKET"],
        'dev/uploads/default_emp_with_noid.csv')
