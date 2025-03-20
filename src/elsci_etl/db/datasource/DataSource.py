class DataSource:
    """
    This is an interface that needs to be implemented by PG-based or Aurora/AWS-based code.
    """
    def create_connection(self):
        raise NotImplementedError('Use implementations, this is an interface!')

    def get_connection_string(self) -> str:
        raise NotImplementedError('Use implementations, this is an interface!')
