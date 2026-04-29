# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pytest
import os
import sys

# --- Diagnostic ---
try:
    import src
    print(f"CONFTEST DEBUG: Imported 'src' module is: {src}")
    print(f"CONFTEST DEBUG: Path of 'src' module: {getattr(src, '__file__', 'N/A (not a file-based module)')}")
    print(f"CONFTEST DEBUG: Contents of 'src' module: {dir(src)}")
except ImportError as e:
    print(f"CONFTEST DEBUG: Failed to import 'src': {e}")
print(f"CONFTEST DEBUG: sys.path: {sys.path}")
# --- End Diagnostic ---

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    Set up necessary environment variables for tests.
    Ensures Celery app can initialize without a real Redis during unit tests.
    """
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0") # Dummy URL for testing
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/0") # For Celery 5+
    # Add any other environment variables needed for tests globallytarel@razorcrest:~/openrelik-worker-photorec$
