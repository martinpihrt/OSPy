import atexit
import os
import shutil
import tempfile


TEST_DATA_DIR = tempfile.mkdtemp(prefix="ospy-tests-")
os.environ["OSPY_DATA_DIR"] = TEST_DATA_DIR
os.environ["OSPY_DISABLE_BACKGROUND_THREADS"] = "1"


@atexit.register
def _remove_test_data():
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
