import boto3
import datetime,dateutil
from dateutil.relativedelta import relativedelta

#Describe your regions here
region_list = ['eu-central-1']

#For creating snapshots
def create_snapshot(volume):
    Description='Created for volume '+volume
    client = boto3.client('ec2')
    response = client.create_snapshot(
        DryRun=False,
        VolumeId=volume,
        Description=Description
    )

def find_snapshots():
    owner='your_id'      #Your owner id is necessary for your snapshots
    client = boto3.client('ec2')
    response = client.describe_snapshots(OwnerIds=[owner])
    snapshot_list=response['Snapshots']

    #Iterate over regions
    for region in region_list:
        print("\n"+"#"*60+"  "+region+"  "+"#"*60+"\n")
        client = boto3.client('ec2', region_name=region)
        #Check running or stopped instances
        response = client.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'stopped']
                }
            ])
        #Iterate over instance(s)
        for r in response['Reservations']:
            for inst in r['Instances']:
                inst_id=inst['InstanceId']
                tags=inst['Tags']
                #Check the Name tag
                for tag in tags:
                    if 'Name' in tag['Key']:
                        ins_tag=(tag['Value'])
                        break
                    else:
                        ins_tag="NA"
                print("-"*30+" "+ins_tag+" ("+inst_id+") "+"-"*30)
                volumes=inst['BlockDeviceMappings']
                volume_temp=[]
                #Iterate over instance's volume(s)
                for volume in volumes:
                    volume=volume['Ebs']['VolumeId']
                    volume_temp.append(volume)
                print("Instance's volumes: ",volume_temp)
                volumes_without_snapshots=[]
                volumes_with_snapshots=[]
                recent_snapshots=[]
                old_snapshots=[]

                #Find the volumes in snapshots
                for volume in volume_temp:
                    for snapshot in snapshot_list:
                        snapshot_volume=snapshot['VolumeId']
                        #Check if volume in snapshot, if so check the date
                        if volume == snapshot_volume:
                            volumes_with_snapshots.append(volume)
                            volumes_with_snapshots=list(set(volumes_with_snapshots))
                            snapshot_date=snapshot['StartTime']
                            a = dateutil.parser.parse(datetime.datetime.now().strftime('%Y-%m-%d'))
                            b = dateutil.parser.parse(datetime.date.strftime(snapshot_date,'%Y-%m-%d'))
                            diff = relativedelta(a, b)
                            snapshot_creation=diff.years*12+diff.months*30+diff.days
                            if snapshot_creation<0:      #Check the snapshots older than 3 days
                                recent_snapshots.append(volume)
                                recent_snapshots=list(set(recent_snapshots))
                            else:
                                old_snapshots.append(volume)
                                old_snapshots=list(set(old_snapshots))

                            if volume in volumes_without_snapshots:
                                volumes_without_snapshots.remove(volume)
                        #Check if volume doesn't have snapshot
                        if (volume != snapshot_volume) and (volume not in volumes_with_snapshots):
                            volumes_without_snapshots.append(volume)
                            volumes_without_snapshots=list(set(volumes_without_snapshots))

                    removed_recent_snapshots=list(set(old_snapshots)-set(recent_snapshots))

                if len(removed_recent_snapshots)>0:
                    print("Volumes with old snapshots: ",removed_recent_snapshots)
                if len(volumes_without_snapshots)>0:
                    print("Volumes without snapshots: ",volumes_without_snapshots)
                print("\n")
                #ask for creating snapshot
                if len(volumes_without_snapshots)>0 or len(removed_recent_snapshots)>0:
                    ask_for_snapshot = input("Do you want to create snapshot of the volumes?: Y/n ")
                if ask_for_snapshot in ['Y','y']:
                    for volume in removed_recent_snapshots:
                        print("Creating snapshot for volume: ",volume)
                        create_snapshot(volume)
                    for volume in volumes_without_snapshots:
                        print("Creating snapshot for volume: ",volume)
                        create_snapshot(volume)

if __name__ == "__main__":
    try:
        find_snapshots()
    except Exception as err:
        print(err)
