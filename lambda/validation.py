import os
import json
import boto3
import pandas as pd
from datetime import datetime
from cerberus import Validator

def lambda_handler(event, context):
    print(event)
    result = {}
    # Create a boto3 S3 client
    s3 = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    bucket_name = "dood-bucket"
    key_name = "source/2019-06-01-15-17-4-events.json"
    source_file_name = event['file_name']

    try:
        file_content = s3.get_object(Bucket=bucket_name, Key=key_name)["Body"].read().decode('utf-8')
        json_content = [cambiar_formato_fechas(json.loads(line), '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M:%S') for line in file_content.splitlines()]
        print("Successfully read")    
    except:
        result['Validation'] = "FAILURE"
        result['Reason'] = "Error while reading Json file in the source bucket"
        result['Location'] = os.environ['source_folder_name']
        print('Error while reading Json')
        return(result)
    result['Validation'] = "SUCCESS"
    result['Location'] = os.environ['source_folder_name']

    transformed_file_name = "s3://" + bucket_name + '/' + os.environ['stage_folder_name'] + '/' + source_file_name
    key_transform = os.environ['stage_folder_name'] + '/' + source_file_name
    if len(json_content) == 0:
        result['Validation'] = "FAILURE"
        result['Reason'] = "NO RECORD FOUND"
        result['Location'] = os.environ['source_folder_name']
        print("Moving file to error folder")
        return(result)
    
    # json_content.to_json(transformed_file_name,
    #               compression='gzip')
    df = pd.json_normalize(json_content)
    # Upload the JSON string to S3
    df.to_csv(transformed_file_name, index=True)
    #s3.put_object(Bucket=bucket_name, Key=key_transform, Body=df)
    #s3_resource.Object(bucket_name, key_name).delete()
    print("Successfuly moved file to  : " + transformed_file_name)
    return result

def cambiar_formato_fechas(data, formato_actual, nuevo_formato, nivel=1):
    for k, v in data.items():
        if isinstance(v, dict) and nivel < 4:
            cambiar_formato_fechas(v, formato_actual, nuevo_formato, nivel+1)
        elif isinstance(v, str):
            try:
                fecha = datetime.strptime(v, formato_actual)
                nueva_fecha = datetime.strftime(fecha, nuevo_formato)
                data[k] = nueva_fecha
            except ValueError:
                pass
    return(data)