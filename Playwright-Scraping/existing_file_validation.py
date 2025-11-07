import os
from typing import Protocol
from pathlib import Path

class ExistingFileValidator(Protocol):
    def is_existing_file(self,file_path:Path)->bool:...

class LocalStorageExistingFileValidator:
    def __init__(self, base_directory: Path) -> None:
        if not base_directory.exists():
            raise Exception('Address provided does not exist')
        
        if not base_directory.is_dir():
            raise Exception('Address provided is not a directory')
        
        self.contained_files = {str(child) for child in base_directory.iterdir()}
    
    def is_existing_file(self,file_path:Path)->bool:
        return str(file_path) in self.contained_files