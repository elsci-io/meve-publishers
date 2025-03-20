from .DataSource import DataSource
from .PasswordBasedDataSource import PasswordBasedDataSource
from elsci_etl.aws import aws_util as aws


class AwsSecretsBasedDataSource(DataSource):
    def __init__(self, db_secret_arn: str):
        secret = aws.get_secret_as_dict(db_secret_arn)
        self._targetDataSource = PasswordBasedDataSource(
            secret['DB_USER'], secret['DB_PASS'], secret['DB_HOST'], secret['DB_PORT'], secret['DB_NAME'],
            secret['DB_SCHEMA']
        )

    def create_connection(self):
        return self._targetDataSource.create_connection()

    def get_connection_string(self) -> str:
        return self._targetDataSource.get_connection_string()