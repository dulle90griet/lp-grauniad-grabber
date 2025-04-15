from unittest.mock import Mock, patch
from datetime import datetime, UTC
import os
import json
import pytest
from moto import mock_aws
import boto3

from src.lp_graun_sifter.post import post


@pytest.fixture
def aws_credentials():
    ''' Mocked AWS credentials for moto testing '''
    os.environ['AWS_ACCESS_KEY_ID'] = "testing"
    os.environ['AWS_SECRET_ACCESS_KEY'] = "testing"
    os.environ['AWS_SECURITY_TOKEN'] = "testing"
    os.environ['AWS_SESSION_TOKEN'] = "testing"
    os.environ['AWS_DEFAULT_REGION'] = "eu-west-2"


@pytest.fixture
def sqs(aws_credentials):
    ''' Return a mocked SQS client '''
    with mock_aws():
        yield boto3.client("sqs", region_name="eu-west-2")


@pytest.fixture
def messages():
    with open("test/data/sample_fetch_output.json", "r", encoding="utf8") as f:
        return json.loads(f.read())


def test_entry_ids_follow_datetime_entry_num_pattern(sqs, messages):
    send_message_spy = Mock(wraps=sqs.send_message_batch)
    sqs.send_message_batch = send_message_spy
    queue_url = sqs.create_queue(QueueName="test-sqs-queue")['QueueUrl']
    test_datetime = datetime.now(UTC)

    post(sqs, queue_url, messages)

    entry_ids = [entry['Id'] for entry in send_message_spy.call_args.kwargs['Entries']]
    for entry_id in entry_ids:
        datepart, numpart = entry_id.split("_")

        # Check datetime in id is reasonably accurate
        entry_datetime = datetime.strptime(datepart, "%Y%m%dT%H%M%S") \
            .replace(tzinfo=UTC)
        delta = entry_datetime - test_datetime
        assert delta.total_seconds() < 10

        # Check numpart contains an integer
        for char in numpart:
            assert char in "0123456789"


def test_entry_ids_zero_indexed_and_in_sequence(sqs, messages):
    send_message_spy = Mock(wraps=sqs.send_message_batch)
    sqs.send_message_batch = send_message_spy
    queue_url = sqs.create_queue(QueueName="test-sqs-queue")['QueueUrl']
    test_datetime = datetime.now(UTC)

    post(sqs, queue_url, messages)

    entry_ids = [entry['Id'] for entry in send_message_spy.call_args.kwargs['Entries']]
    for i, entry_id in enumerate(entry_ids):
        entry_num = int(entry_id.split("_")[1])
        assert i == entry_num


# test_messages_in_original_sequence

# test_entry_message_bodies_formed_without_loss

# test_max_10_messages_posted

# test_posted_messages_present_in_SQS_queue

# test_SQS_queue_stores_messages_without_loss
