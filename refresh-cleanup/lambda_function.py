import json
import boto3
import re


def lambda_handler(event, context):
    instance_list = []
    if event["detail-type"] == "Scheduled Event":
        region = event["region"]
        rds_client = boto3.client('rds', region_name=region)
        print(f"going through region {region}")
        result = rds_client.describe_db_instances()["DBInstances"]
        for instance in result:
            db_identifier = instance["DBInstanceIdentifier"]
            if re.search("-(old)-(es-\d+)-(\d+)", db_identifier):
                instance_list.append(db_identifier)
    return instance_list
