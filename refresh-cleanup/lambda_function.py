import json
import boto3
import re
import time
import datetime


def deleteRDS(instance: dict, rds_client: boto3) -> bool:
    try:
        identifier = instance['DBInstanceIdentifier']
        response = rds_client.delete_db_instance(
            DBInstanceIdentifier=identifier,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True)["DBInstance"]
        time.sleep(2) # Waiting 2 sec to make sure AWS corrects instance status
        response = rds_client.describe_db_instances(DBInstanceIdentifier=identifier)["DBInstances"]
        if response[0]["DBInstanceStatus"] == "deleting":
            print(f"Successfully started deleting {identifier}")
        return True
    except Exception as E:
        print(E)
        return False


def checkInstance(instance: dict):
    instance_name = instance['DBInstanceIdentifier']
    if not instance["DBInstanceStatus"] == "stopped":
        print(f"instance {instance_name} is not in status: -stopped- but in status: -{instance['DBInstanceStatus']}-")
        return False
    instance_restart_time: datetime.datetime = instance["AutomaticRestartTime"]
    irt_formatted = instance_restart_time.strftime("%d/%m/%Y")
    date_today = datetime.date.today().strftime("%d/%m/%Y")
    if not date_today == irt_formatted:
        print(f"{instance_name} deletion date is {irt_formatted} and not today {date_today}")
        return False
    return True


def lambda_handler(event, context):
    instance_list = []
    if event["detail-type"] == "Scheduled Event":
        region = event["region"]
        rds_client = boto3.client('rds', region_name=region)
        print(f"going through region {region}")
        result = rds_client.describe_db_instances()["DBInstances"]
        for instance in result:
            db_identifier = instance["DBInstanceIdentifier"]
            if not re.search("-(old)-(es-\d+)-(\d+)", db_identifier):
                continue
            if checkInstance(instance):
                print(f"Trying to delete {db_identifier}")
                if deleteRDS(instance, rds_client):
                    instance_list.append("db_identifier")
    if instance_list:
        print(f"Deleting instance: {instance_list}")
        return f"Deleting instance: {instance_list}"
    print(f"Nothing to delete")
    return f"Nothing to delete"
