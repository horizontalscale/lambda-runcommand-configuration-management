"""
Unit Tests for trigger_run_command Lambda function
"""
import pytest
from botocore.exceptions import ClientError
from mock import MagicMock, patch
from main import log_event_and_context
from main import find_artifact
from main import ssm_commands
from main import codepipeline_success
from main import codepipeline_failure
from main import find_instances
from main import send_run_command
from freezegun import freeze_time

def test_log_event_and_context():
    """
    Test the log_event_and_context function
    """
    assert log_event_and_context

def test_find_artifact():
    """
    Test the log_event_and_context function with valid event
    """
    event = {
        'CodePipeline.job': {
            'data': {
                'inputArtifacts': [{
                    'location': {
                        's3Location': {
                            'objectKey': 'test/key',
                            'bucketName': 'bucket'
                        }
                    }
                }]
            }
        }
    }
    assert find_artifact(event) == 's3://bucket/test/key'

def test_find_artifact_invalid():
    """
    Test the log_event_and_context function with invalid event
    """
    event = {}
    with pytest.raises(KeyError):
        assert find_artifact(event) == 'blah'

@freeze_time('2016-01-01')
def test_ssm_commands():
    """
    Test the ssm_commands function
    """
    artifact = 'bucket/test/key'
    commands = [
        'aws configure set s3.signature_version s3v4',
        'aws s3 cp bucket/test/key /tmp/20160101000000.zip --quiet',
        'unzip -qq /tmp/20160101000000.zip -d /tmp/20160101000000',
        'bash /tmp/20160101000000/generate_inventory_file.sh',
        'ansible-playbook -i "/tmp/inventory" /tmp/20160101000000/ansible/playbook.yml'
    ]
    assert ssm_commands(artifact) == commands

@patch('boto3.client')
def test_codepipeline_success(mock_client):
    """
    Test the codepipeline_success function with valid data
    """
    codepipeline = MagicMock()
    mock_client.return_value = codepipeline
    codepipeline.put_job_success_result.return_value = True
    assert codepipeline_success(1) == True

@patch('boto3.client')
def test_codepipeline_success_invalid(mock_client):
    """
    Test the codepipeline_success function when a boto exception occurs
    """
    codepipeline = MagicMock()
    mock_client.return_value = codepipeline
    err_msg = {
        'Error': {
            'Code': 400,
            'Message': 'Boom!'
        }
    }
    codepipeline.put_job_success_result.side_effect = ClientError(err_msg, 'Test')
    assert codepipeline_success(1) == False

@patch('boto3.client')
def test_codepipeline_failure(mock_client):
    """
    Test the codepipeline_failure function with valid data
    """
    codepipeline = MagicMock()
    mock_client.return_value = codepipeline
    codepipeline.put_job_failure_result.return_value = True
    assert codepipeline_failure(1, 'blah') == True

@patch('boto3.client')
def test_codepipeline_failure_invalid(mock_client):
    """
    Test the codepipeline_failure function when a boto exception occurs
    """
    codepipeline = MagicMock()
    mock_client.return_value = codepipeline
    err_msg = {
        'Error': {
            'Code': 400,
            'Message': 'Boom!'
        }
    }
    codepipeline.put_job_failure_result.side_effect = ClientError(err_msg, 'Test')
    assert codepipeline_failure(1, 'blah') == False

@patch('boto3.client')
def test_find_instances(mock_client):
    """
    Test the find_instances function without errors
    """
    ec2 = MagicMock()
    instances = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'abcdef-12345'
            }]
        }]
    }
    mock_client.return_value = ec2
    ec2.describe_instances.return_value = instances
    assert find_instances() == ['abcdef-12345']

@patch('boto3.client')
def test_send_run_command(mock_client):
    """
    Test the send_run_command function without errors
    """
    ssm = MagicMock()
    mock_client.return_value = ssm
    ssm.send_command.return_value = True
    assert send_run_command(['abcdef-12345'], ['blah']) == 'success'

@patch('boto3.client')
def test_send_run_command_invalid(mock_client):
    """
    Test the send_run_command function when a boto exception occurs
    """
    ssm = MagicMock()
    mock_client.return_value = ssm
    err_msg = {
        'Error': {
            'Code': 400,
            'Message': 'Boom!'
        }
    }
    ssm.send_command.side_effect = ClientError(err_msg, 'Test')
    assert send_run_command(['abcdef-12345'], ['blah']) != 'success'