import json
import logging
import uuid
import os
from datetime import datetime
import boto3
import pandas as pd
from io import StringIO
from treelib import Tree, Node

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
s3 = boto3.client('s3')

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body":     json.dumps("ok"),
}

ERROR_RESPONSE = {"statusCode": 400,
                  "body": json.dumps("Oops, something went wrong!")}


def get_hierarchical_data(event, context):
    query_params = (
        event.get("queryStringParameters")
        if event.get("queryStringParameters") is not None
        else {}
    )
    file_key = query_params.get("file_key", "")

    if not file_key:
        return ERROR_RESPONSE
    try:
        OK_RESPONSE["body"] = json.dumps(
            prepareTreeData(os.environ["S3_BUCKET"], file_key))
        return OK_RESPONSE
    except Exception as e:
        logging.error(e)
        return ERROR_RESPONSE


def export_hierarchical_data2S3(event, context):
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']
        logger.info('Reading {} from {}'.format(file_key, bucket_name))
        df = pd.DataFrame(prepareTreeData(bucket_name, file_key))
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, header=False, index=False)
        s3.put_object(Body=csv_buffer.getvalue(),
                      Bucket=bucket_name,
                      Key="{}/output/{}/{}".format(os.environ["STAGE"],
                                                   datetime.now().strftime("%d-%m-%Y-%H-%M-%S"),
                                                   os.path.basename(file_key)))
    except Exception as e:
        logging.error(e)


def prepareTreeData(bucket_name, file_key):
    csv = s3.get_object(Bucket=bucket_name, Key=file_key)
    org_df = pd.read_csv(csv['Body'], skip_blank_lines=True, header=0,
                         usecols=["name", "emp_id", "manager_id"],
                         names=["name", "emp_id", "manager_id"],
                         dtype=object)

    org_df = org_df[pd.notnull(org_df['emp_id'])]
    org_df.loc[(org_df['manager_id'].isin(org_df["emp_id"]) |
                org_df['manager_id'].isna()), 'manager_valid'] = True
    org_df["manager_valid"].fillna(False, inplace=True)
    org_df["manager_id"].fillna('', inplace=True)

    my_org_tree = Tree()
    my_org_tree.create_node("Root", "1")

    show_unknown_manager = False
    for index, row in org_df.iterrows():
        my_org_tree.create_node(row['name'], str(row['emp_id']), parent="1", data={
                                "name": str(row['emp_id']), "id": str(row['emp_id'])})
        if not row['manager_valid']:
            show_unknown_manager = True

    if show_unknown_manager:
        my_org_tree.create_node("Unknown Manager", "1.1", parent="1", data={
                                "name": "Unknown Manager", "id": "1.1"})

    for index, row in org_df.iterrows():
        if row['manager_id'] and row['manager_valid']:
            parent = str(row['manager_id'])
        elif not row['manager_valid']:
            parent = "1.1"
        else:
            parent = "1"
        my_org_tree.move_node(str(row['emp_id']), parent)

    org_dict = my_org_tree.to_dict(with_data=True)
    org_obj_list = org_dict["Root"]['children']
    return convertRawData(my_org_tree, org_obj_list)


def convertRawData(my_org_tree, org_obj_list):
    emp_list = []

    def get_depth(id):
        node = my_org_tree.get_node(str(id))
        return my_org_tree.depth(node)

    def flatten_emp_list(d):
        if isinstance(d, (list)):
            for l in d:
                flatten_emp_list(l)
        else:
            for k, v in d.items():
                if v.get("data"):
                    temp_dict = {}
                    for n in range(1, my_org_tree.depth() + 1):
                        current_node = get_depth(v["data"]["id"])
                        if n != current_node:
                            temp_dict.update({"level_" + str(n): ""})
                        else:
                            temp_dict.update({"level_" + str(current_node): k})
                    emp_list.append(temp_dict)
                if v.get("children"):
                    flatten_emp_list(v['children'])
    flatten_emp_list(org_obj_list)
    return emp_list
