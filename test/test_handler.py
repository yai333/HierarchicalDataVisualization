# emp_handler.py
import os
import json
from src import handler


# upload default csv and put converted csv to s3 output bucket
def test_export_hierarchical_data2S3(s3_client, create_bucket, upload_default_csv):
    event = {"Records": [
        {"s3": {

             "bucket": {
                 "name": "aiyi.data.visualization"
             },
             "object": {
                 "key": "dev/uploads/emp.csv"
             }
             }
         }
    ]}
    handler.export_hierarchical_data2S3(event, {})
    s3_bucket = "aiyi.data.visualization"
    s3_result = s3_client.list_objects_v2(Bucket=s3_bucket)
    assert s3_result["Contents"][0]['Key'].find('emp.csv') >= 0


# one level hierarchy data visualization
def test_get_hierarchical_data_two_levels(s3_client, create_bucket,
                                          upload_two_levels_csv):
    event = {"body": {},
             "queryStringParameters": {"file_key": "dev/uploads/two_levels.csv"}}
    response = handler.get_hierarchical_data(event, {})
    assert response["statusCode"] == 200
    response_body = response["body"]
    expect_output = json.dumps([{'level_1': 'Jamie', 'level_2': ''},
                                {'level_1': '', 'level_2': 'Alan'},
                                {'level_1': '', 'level_2': 'Steve'}])
    assert response_body == expect_output


# two level hierarchy data visualization
def test_get_hierarchical_data_three_levels(s3_client, create_bucket,
                                            upload_three_levels_csv):
    event = {"body": {},
             "queryStringParameters": {"file_key": "dev/uploads/three_levels.csv"}}
    response = handler.get_hierarchical_data(event, {})
    assert response["statusCode"] == 200
    response_body = response["body"]
    expect_output = json.dumps([{'level_1': 'Jamie', 'level_2': '', 'level_3': ""},
                                {'level_1': '', 'level_2': 'Alan', 'level_3': ""},
                                {'level_1': '', 'level_2': '', 'level_3': "Alex"}])
    assert response_body == expect_output


# validate two level hierarchy data with invalid manager
def test_get_hierarchical_with_unknown_manager(s3_client, create_bucket,
                                               upload_default_emp_with_noid):
    event = {"body": {},
             "queryStringParameters": {"file_key": "dev/uploads/default_emp_with_noid.csv"}}
    response = handler.get_hierarchical_data(event, {})
    assert response["statusCode"] == 200
    response_body = response["body"]
    expect_output = json.dumps([{"level_1": "Jamie", "level_2": ""},
                                {"level_1": "Unknown Manager", "level_2": ""},
                                {"level_1": "", "level_2": "John"}])
    assert response_body == expect_output


# validate if csv file not found in csv
def test_get_hierarchical_with_unknown_manager(s3_client, create_bucket,
                                               upload_default_emp_with_noid):
    event = {"body": {},
             "queryStringParameters": {"file_key": "dev/uploads/random.csv"}}
    response = handler.get_hierarchical_data(event, {})
    assert response["statusCode"] == 400
