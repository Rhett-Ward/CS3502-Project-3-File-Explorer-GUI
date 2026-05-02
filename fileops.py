#fileops.py
#File system operations for CS 3502 project 3
#Rhett Ward


import os
import shutil
from pathlib import Path


def list_directory(path):
    entries = []
    for name in os.listdir(path): # for each name in list of names
        full = os.path.join(path, name)
        try:
            info = os.stat(full) #metadata for name
            entries.append({
                "name": name,
                "path": full,
                "is_dir": os.path.isdir(full),
                "size": info.st_size,
                "mtime": info.st_mtime,
            })
        except (PermissionError, OSError):
            entries.append({
                "name": name,
                "path": full,
                "is_dir": False,
                "size": 0,
                "mtime": 0,
            })
    return entries


def read_file(path):
    #reads file at exact path
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    #writes to a file at exact path. can overwrite if same name as existing file
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_empty_file(path):
    #create file, fail if arleady exists
    with open(path, "x", encoding="utf-8") as f:
        pass


def create_directory(path):
    # os.mkdir is python equivalent to terminal mkdir
    os.mkdir(path)


def delete_file(path):
    # deletes file by unlinking exact path
    os.remove(path)


def delete_empty_directory(path):
    # runs terminal rmdir but in python, only works on empty directories
    os.rmdir(path)


def delete_directory_recursive(path):
    #deletes a directory and all files and subdirectories in it.
    shutil.rmtree(path)


def rename_path(old_path, new_path):
    # functional equivalent to terminal MV
    os.rename(old_path, new_path)


def copy_path(src, dst):
    #shutil kinda the goat
    if os.path.isdir(src):
        #copies a directory and its files and subdirectories in the same way that shutil.rmtree deletes a directory and its files and subdirectories
        shutil.copytree(src, dst)
    else:
        #copy 2 to preserve metadata
        shutil.copy2(src, dst)


def move_path(src, dst):
    #
    shutil.move(src, dst)


def get_file_info(path):
    # simplistic equivalent of right clicking a file and then clicking properties in the pop up menu.
    info = os.stat(path)
    return {
        "size": info.st_size,
        "mtime": info.st_mtime,
        "ctime": info.st_ctime,
        "atime": info.st_atime,
        "mode": info.st_mode,
        "is_dir": os.path.isdir(path),
        "readable": os.access(path, os.R_OK),
        "writable": os.access(path, os.W_OK),
    }


def is_directory_empty(path):
    # helper method for rmdir to prevent attempts to use rmdir on non empty directory.
    return len(os.listdir(path)) == 0
