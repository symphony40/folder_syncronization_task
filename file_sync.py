import argparse
import time
import os
import logging
import shutil
import hashlib

def set_up_logging(log_file_path):
    try:
        #setting up logfile
        log_file_dir = os.path.dirname(log_file_path)
        if log_file_dir and not os.path.exists(log_file_dir):
            os.makedirs(log_file_dir)
        logging.basicConfig(filename=log_file_path,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
        #setting up logging to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)
    except Exception as e:
        print(f"Failed to initialize logging: {e}")
        exit(1)

def calculate_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def check_args(args):
    source_abs = os.path.abspath(args.source_path)
    replica_abs = os.path.abspath(args.replica_path)

    if os.path.commonpath([source_abs]) == os.path.commonpath([source_abs, replica_abs]):
        logging.error("Source and replica paths must not overlap.")
        exit(1)

    if not os.path.exists(args.source_path):
        print("Source path invalid")
        exit(1)

    if not os.access(args.source_path, os.R_OK):
        print("Source file is not readable")
        exit(1)

    if not os.path.exists(args.replica_path):
        try:
            os.makedirs(args.replica_path)
        except Exception as e:
            print(f"Failed to create replica directory: {e}")
            exit(1)
    else:
        if not os.path.isdir(args.replica_path):
            print("Replica path exists but is not a directory")
            exit(1)
    
def sync_new_or_updated_files(args):
     for root, dirs, files in os.walk(args.source_path):
        relative_path = os.path.relpath(root, args.source_path)
        replica_path = os.path.join(args.replica_path, relative_path)
        
        if not os.path.exists(replica_path):
            os.makedirs(replica_path)
            logging.info(f"Created directory: {replica_path}")
        
        for file in files:
            source_file = os.path.join(root, file)
            replica_file = os.path.join(replica_path, file)
            
            if not os.path.exists(replica_file) or calculate_md5(source_file) != calculate_md5(replica_file):
                shutil.copy2(source_file, replica_file)
                logging.info(f"Copied file: {source_file} -> {replica_file}")

def remove_extra_files_and_directories(args):
     for root, dirs, files in os.walk(args.replica_path):
        relative_path = os.path.relpath(root, args.replica_path)
        source_path = os.path.join(args.source_path, relative_path)
        
        for file in files:
            replica_file = os.path.join(root, file)
            source_file = os.path.join(source_path, file)
            if not os.path.exists(source_file):
                os.remove(replica_file)
                logging.info(f"Removed file: {replica_file}")
        
        for dir in dirs:
            replica_dir = os.path.join(root, dir)
            source_dir = os.path.join(source_path, dir)
            if not os.path.exists(source_dir):
                shutil.rmtree(replica_dir)
                logging.info(f"Removed directory: {replica_dir}")

def sync_loop(args):
    while True:
        sync_new_or_updated_files(args)
        remove_extra_files_and_directories(args)
        time.sleep(args.sync_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_path", help="path to the folder to sync")
    parser.add_argument("replica_path", help="path to the replica folder")
    parser.add_argument("sync_interval", help="syncronization interval (in seconds)", type=int)
    parser.add_argument("log_file_path", help="path to log file")
    args = parser.parse_args()
    set_up_logging(args.log_file_path)
    check_args(args)
    sync_loop(args)