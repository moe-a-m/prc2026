import pytest

from prc import paths


@pytest.fixture(scope="session")
def con():
    if not paths.DB.exists():
        pytest.skip("data/prc.duckdb not built (run `make ingest clean`)")
    from prc import db
    c = db.connect(read_only=True)
    yield c
    c.close()
