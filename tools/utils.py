import os
import re

directory_path = "files/"
version_pattern = r"v\d+\.\d+\.\d+"
default_version = "v0.0.0"

def get_file_version(title, directory_path=directory_path, version_pattern=version_pattern):
    pattern = f"{title}.*"
    version = None

    # Check if the file exists in the directory
    file_exists = any(re.match(pattern, file) for file in os.listdir(directory_path))

    if file_exists:
        print(f"A file with the title '{title}' exists in the directory.")

        # Extract the version from the file name
        for file in os.listdir(directory_path):
            if re.match(pattern, file):
                version_match = re.search(version_pattern, file)
                if version_match:
                    version = version_match.group()
                    break

    return version

def increment_version(version):
    major, minor, patch = map(int, version.lstrip('v').split('.'))

    patch += 1

    if patch == 10:
        patch = 0
        minor += 1

    if minor == 10:
        minor = 0
        major += 1

    new_version = f"v{major}.{minor}.{patch}"
    return new_version