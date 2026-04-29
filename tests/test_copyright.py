    # Copyright 2026 Google LLC
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #    https://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License.

    import datetime
    import os
    from pathlib import Path

    def test_copyright_headers():
        """Verify that all python files have the correct copyright header for the current year."""
        repo_root = Path(__file__).parent.parent
        current_year = datetime.date.today().year
        expected_header = f"# Copyright {current_year} Google LLC"

        for root, dirs, files in os.walk(repo_root):
            # Skip .git and other hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        first_line = f.readline().strip()
                        assert first_line == expected_header, f"{file_path} is missing the correct copyright header or year."
