import gzip
import urllib.parse
from pathlib import Path

import requests
from ord_schema.message_helpers import ORD_DATA_URL, id_filename
from ord_schema.proto import dataset_pb2

_WORK_DIR = './ord-datasets'

def download_dataset(dataset_id: str, timeout: float = 10.):
    """Loads a dataset from the ord-data repository.

    Args:
        dataset_id: Dataset ID.
        timeout: Number of seconds to wait before timing out the request.

    Returns:
        Dataset message.

    Raises:
        RuntimeError: If the request fails.
        ValueError: If the dataset ID is invalid.
    """
    from ord_schema import validations  # pylint: disable=cyclic-import,import-outside-toplevel

    if not validations.is_valid_dataset_id(dataset_id):
        raise ValueError(f"Invalid dataset ID: {dataset_id}")
    filename = _dataset_filename(dataset_id)
    url = urllib.parse.urljoin(ORD_DATA_URL, id_filename(filename))
    print("Downloading " +url)
    response = requests.get(url, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(f"Request {url} failed with status {response.status_code}")
    path = Path(_WORK_DIR)
    if not path.exists():
        path.mkdir()
    with open(f"{_WORK_DIR}/{filename}", 'wb') as f:
        f.write(response.content)

def get_dataset(dataset_id: str, timeout: float = 10.0) -> dataset_pb2.Dataset:
    path = Path(_WORK_DIR, _dataset_filename(dataset_id))
    if not path.exists():
        download_dataset(dataset_id, timeout)
    print(f"Opening {path}")
    with open(path, 'rb') as f:
        return dataset_pb2.Dataset.FromString(gzip.decompress(f.read()))

def _dataset_filename(dataset_id: str) -> str:
    return f"{dataset_id}.pb.gz"