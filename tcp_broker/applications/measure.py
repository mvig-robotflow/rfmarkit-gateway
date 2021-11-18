import logging
import os
import zipfile
import glob
import multiprocessing as mp
import time

from typing import Dict

from config import OSS_ACCESSKEY, OSS_BUCKET, OSS_ENDPOINT, OSS_SECRETKEY, PROCESSOR_APIHOST, DEBUG, DATA_DIR

from tasks import tcp_listen_task
from helpers import invoke_data_process_task, upload_file_oss
from .control import control

logging.basicConfig(level=logging.DEBUG) if DEBUG else logging.basicConfig(level=logging.INFO)

def measure(port: int, measurement_name: str):
    # Listen TCP
    client_addr_queue = mp.Queue(maxsize=32)

    tcp_listen_task_process = mp.Process(None, tcp_listen_task, "tcp_listen_task", ('0.0.0.0', port, measurement_name, client_addr_queue,))
    tcp_listen_task_process.start()
    control(port, client_addr_queue)

    # FIXME: If exit control app with quit, the tcp_listen_task will still be running and waiting Keyboard interrupt. This interrupt will also be sent to current process, thus might cause trouble
    try:
        tcp_listen_task_process.join()
    except KeyboardInterrupt:
        time.sleep(0.1)
        tcp_listen_task_process.join()

    # Write readme
    measurement_basedir = os.path.join(DATA_DIR, measurement_name)
    experiment_logs = input("Experiment logs:\n> ")
    logging.info(f"Writting README")
    with open(os.path.join(measurement_basedir, 'README'), 'w') as f:
        f.write(measurement_name + '\n')
        f.write(experiment_logs + '\n')


    # Create zip archive
    logging.info(f"Creating zip archive")
    archive_filename = os.path.join('/tmp', f'{measurement_name}.zip')
    filenames = glob.glob(os.path.join(measurement_basedir,'*'))
    with zipfile.ZipFile(archive_filename, 'w', zipfile.ZIP_DEFLATED) as f:
        for filename in filenames:
            f.write(filename, os.path.join(measurement_name,os.path.basename(filename)))
    
    # Upload to Object Storage
    logging.info(f"Uploading to oss")
    try:
        ret: Dict = upload_file_oss(OSS_ENDPOINT, OSS_BUCKET, OSS_ACCESSKEY, OSS_SECRETKEY, archive_filename, f'{measurement_name}.zip')
    except Exception as err:
        logging.error(f"Exception occurs when uploading: {err}")
        ret = {'status': False}

    # Invoke process task if PROCESSOR_APIHOST is defined in environment
    if PROCESSOR_APIHOST:
        if not ret['status']:
            logging.warn(f"Unable to upload {measurement_name} : \n{ret['error']}")
        else:
            logging.info(f"Successfully uploaded: \n{ret['object_name']}")
            try:
                if DEBUG:
                    invoke_data_process_task(PROCESSOR_APIHOST, {"value": ret}) # Mimic OpenWhisk format invoke
                else: 
                    invoke_data_process_task(PROCESSOR_APIHOST, ret)

            except Exception as err:
                logging.error(f"Exception occurs when invoking: {err}")
                ret = {'status': False}

    # Delete archive
    os.remove(archive_filename)