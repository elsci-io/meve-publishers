import logging

import psycopg2
from psycopg2.extras import DictCursor

from elsci_etl.db.datasource.DataSource import DataSource


class PasswordBasedDataSource(DataSource):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, user: str, password: str, host: str, port: int, dbname: str, schema: str):
        self._port = port
        self._host = host
        self._password = password
        self._user = user
        self._dbname = dbname
        self._schema = schema

    def create_connection(self):
        self.LOGGER.debug("Connecting to DB: " + self._get_connection_string("***"))
        return psycopg2.connect(
            database=self._dbname,
            user=self._user, password=self._password,
            host=self._host, port=self._port,
            options=f"-c search_path={self._schema}",
            cursor_factory=DictCursor
        )

    def get_connection_string(self) -> str:
        return self._get_connection_string(self._password)

    def _get_connection_string(self, password: str) -> str:
        # Seems like `schema` isn't really standardized - it's only Yoyo who uses this parameter. So if we
        # at some point would need it for other tools, we'd have to add even more parameters with different
        # names but the same value
        return f"postgresql://{self._user}:{password}@{self._host}:{self._port}/{self._dbname}?schema={self._schema}"
