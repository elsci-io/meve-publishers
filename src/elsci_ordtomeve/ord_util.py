import gzip
import urllib.parse
from pathlib import Path

import requests
from ord_schema.message_helpers import ORD_DATA_URL, id_filename
from ord_schema.proto import dataset_pb2, reaction_pb2

_WORK_DIR = './ord-datasets'

PARQUET_SUFFIX = '.parquet'
PROTOBUF_SUFFIX = '.pb.gz'


def download_dataset(dataset_id: str, timeout: float = 10.) -> Path:
    """Loads a dataset from the ord-data repository.

    Args:
        dataset_id: Dataset ID.
        timeout: Number of seconds to wait before timing out the request.

    Returns:
        The path to the downloaded file.

    Raises:
        RuntimeError: If the request fails for both PB and Parquet.
        ValueError: If the dataset ID is invalid.
    """
    from ord_schema import validations  # pylint: disable=cyclic-import,import-outside-toplevel

    if not validations.is_valid_dataset_id(dataset_id):
        raise ValueError(f"Invalid dataset ID: {dataset_id}")

    # The official documentation says:
    # Datasets in the GH repository are stored as .pb.gz; most also have a Parquet sibling.
    # New submissions arrive as .pb.gz only, so their Parquet versions are backfilled
    # with scripts/convert_to_parquet.py.
    # The script globs every data/**/*.pb.gz, merges the known de-shard groups
    # (the uspto-grants-YYYY_MM monthly buckets and the C8SC04228D shards) into single outputs,
    # converts everything else 1:1 (carrying the existing dataset_id),
    # and skips any output that already exists — so it is safe to re-run and writes only what is missing.
    #
    # https://github.com/open-reaction-database/ord-data

    # This means the dataset should always present in PB format, so try PB first,
    # and if it fails, try Parquet (but I am not sure if the parquet version will be present in that case).

    downloaded = _download_dataset(_pb_dataset_filename(dataset_id), timeout=timeout)
    if not downloaded:
        downloaded = _download_dataset(_parquet_dataset_filename(dataset_id), timeout=timeout)
    if downloaded:
        return downloaded
    raise RuntimeError(f"Failed to download dataset {dataset_id} in either PB or Parquet format.")


def get_dataset(dataset_id: str, timeout: float = 10.0) -> dataset_pb2.Dataset:
    local_path = _find_local_dataset(dataset_id)
    if not local_path:
        local_path = download_dataset(dataset_id, timeout=timeout)

    if local_path.suffix == PARQUET_SUFFIX:
        return get_dataset_from_parquet(local_path)
    elif ''.join(local_path.suffixes) == PROTOBUF_SUFFIX:
        with open(local_path, 'rb') as f:
            return dataset_pb2.Dataset.FromString(gzip.decompress(f.read()))
    else:
        raise RuntimeError(f"Unsupported file format for dataset {dataset_id}: {local_path}")


def get_dataset_from_parquet(path: Path) -> dataset_pb2.Dataset:
    """Reads a dataset from a Parquet file."""
    import pandas as pd
    print(f"Opening Parquet {path}")
    df = pd.read_parquet(path)
    dataset = dataset_pb2.Dataset()
    for _, row in df.iterrows():
        reaction = reaction_pb2.Reaction.FromString(row['reaction'])
        dataset.reactions.append(reaction)
    return dataset


def _download_dataset(file_name: str, timeout: float = 10.0) -> Path | None:
    path = Path(_WORK_DIR)
    if not path.exists():
        path.mkdir(parents=True)

    file_url = urllib.parse.urljoin(ORD_DATA_URL, id_filename(file_name))
    response = requests.get(file_url, timeout=timeout)
    if response.status_code == 200:
        print(f"Downloading {file_url}")
        target_path = path / file_name
        with open(target_path, 'wb') as f:
            f.write(response.content)
        return target_path
    return None


def _find_local_dataset(file_name: str) -> Path | None:
    local_path = Path(_WORK_DIR, _pb_dataset_filename(file_name))
    if local_path.exists():
        return local_path
    else:
        local_path = Path(_WORK_DIR, _parquet_dataset_filename(file_name))
        if local_path.exists():
            return local_path
        else:
            return None


def _pb_dataset_filename(dataset_id: str) -> str:
    return f"{dataset_id}{PROTOBUF_SUFFIX}"


def _parquet_dataset_filename(dataset_id: str) -> str:
    return f"{dataset_id}{PARQUET_SUFFIX}"
