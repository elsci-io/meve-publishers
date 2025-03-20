import json

import boto3 as boto


def get_secret_as_dict(secret_arn: str) -> dict:
    s = boto.session.Session()
    secrets = s.client('secretsmanager')
    secret_json = secrets.get_secret_value(SecretId=secret_arn)['SecretString']
    return json.loads(secret_json)
