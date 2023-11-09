# For testing
import boto3
from botocore.exceptions import ClientError
import aws_sso
import pprint
import datetime
"""
Old script does:
Gets environment vars with a list of regions to ignore

Go through every region that is not ignored

For each region:
Describe db snapshots
if snapshot starts with "daily-backup" and snapshot is available it adds it to a list of snapshots

If there's mulitple snapshots, the oldest ones are being deleted.
"""
event = {"detail-type": "Scheduled Event", "region": "eu-central-1"}

def snapshot_sort(snapshots: list[dict]) -> list[dict]:
    """Sort snapshots pr customer instance"""
    return_dict = {}
    snapshot_dict = {}
    for snapshot in snapshots:
        instance_id = snapshot["DBInstanceIdentifier"]
        snapshot_id = snapshot["DBSnapshotIdentifier"]
        creation_time = snapshot["OriginalSnapshotCreateTime"]
        snap_state = snapshot["Status"]
        if snap_state != "available":
            print(f"Snapshot {snapshot_id} is not in state available but in: {snap_state}")
            continue
        if not instance_id in return_dict:
            return_dict[instance_id] = []
        snapshot_dict = {
            "DBInstanceIdentifier": instance_id,
            "DBSnapshotIdentifier": snapshot_id,
            "OriginalSnapshotCreateTime": creation_time,
        }
        return_dict[instance_id].append(snapshot_dict)
    return return_dict

def delete_oldest_snapshot(snapshots: list[dict], client: boto3.Session.client) -> None:
    """Find the newest snapshot and delete all old ones if multiple"""
    newest_snap = None
    # Find newest snap:
    for snap in snapshots:
        if not newest_snap:
            newest_snap = snap
            continue
        if snap["OriginalSnapshotCreateTime"] > newest_snap["OriginalSnapshotCreateTime"]:
            newest_snap = snap
    for snap in snapshots:
        snap_id = snap["DBSnapshotIdentifier"]
        if snap_id == newest_snap["DBSnapshotIdentifier"]:
            print(f"+ KEEPING NEWEST: {snap_id}")
            continue
        try:
            response = client.delete_db_snapshot(DBSnapshotIdentifier=snap_id)
            print(f"- DELETING OLD: {snap_id}")
            if response['DBSnapshot']['Status'] == "deleted":
                print(f"- {snap_id} HAS BEEN DELETED")
            elif response['DBSnapshot']['Status'] == "deleting":
                print(f"- {snap_id} IS BEING DELETED")
        except ClientError as e:
            if e.response['Error']['Code'] == 'DBInstanceNotFound':
                print("DB instance not found. Make sure the instance exists.")
            elif e.response['Error']['Code'] == 'InvalidDBSnapshotState':
                print("The snapshot state is invalid for this operation.")
            else:
                print("An error occurred:", e) 




def lambda_handler(event, context):
    if event["detail-type"] == "Scheduled Event":
        region = event["region"]
        profile="customer-workload-dr-exerp-admin" # Remove after testing
        aws_sso.validate_sso_token(profile=profile) # Remove after testing
        session = boto3.Session(profile_name=profile)
        client = session.client('rds', region_name=region)
        
        snapshots = client.describe_db_snapshots()['DBSnapshots']
        if not snapshots:
            print(f"Something went wrong when fetching snapshots")
            exit(1)
        sorted_snaps = snapshot_sort(snapshots)
        for customer in sorted_snaps:
            if len(sorted_snaps[customer]) > 1:
                print(f"Found multiple snapshots from: {str(customer).upper()}")
                delete_oldest_snapshot(sorted_snaps[customer], client)
                print("\n")
            else:
                print(f"Nothing to delete from customer: {str(customer).upper()}")
        print(f"Snapshot cleanup complete.")
        

# Remove after testing
if __name__ == "__main__":
    context = ""
    lambda_handler(event,context)