Meve Publishers
---

Here are the ETLs to read the data about molecules from different data sources and import them into [Meve](https://elsci.io/meve/index.html) as events.

# Running ETLs

To run any of the ETLs:

1. Install [uv](https://github.com/astral-sh/uv) build tool and run: `uv venv && uv sync && uv build`
2. (Optional) In PyCharm mark `src` as Sources Root and `test` as Test Sources Root

# Open Reaction Database

Currently, only the ETL from the [Open Reaction Database](https://open-reaction-database.org/) is available publicly. To run it:

```shell
export MEVE_BASE_URL=https://host.name/
export MEVE_USER_NAME=basic_auth_username
export MEVE_USER_PASSWORD=basic_auth_password

PYTHONPATH=src python src/elsci_ordtomeve/ord_to_meve.py
```

You can modify the list of datasets to import in [datasets.txt](./src/elsci_ordtomeve/datasets.txt). The actual data is coming from [ord-data](https://github.com/open-reaction-database/ord-data).