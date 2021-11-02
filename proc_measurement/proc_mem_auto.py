"""proc_mem_auto.py"""
from typing import Any, Dict, List, Tuple
import os
import zipfile
import logging
import glob
import shutil
import asyncio

from minio import Minio
from helpers import download_file_oss, convert_measurement, upload_file_oss

OSS_ENDPOINT = os.environ['OSS_ENDPOINT']
OSS_SRC_BUCKET = os.environ['OSS_SRC_BUCKET']
OSS_DST_BUCKET = os.environ['OSS_DST_BUCKET']
OSS_ACCESSKEY = os.environ['OSS_ACCESSKEY']
OSS_SECRETKEY = os.environ['OSS_SECRETKEY']

logging.basicConfig(level=logging.INFO)


async def convert(object_name: str) -> Tuple[bool, str, Dict[str, Any]]:
    measurement_name = object_name.split('.')[0]
    measurement_basedir = os.path.join('.', measurement_name)
    measurement_filename = object_name
    
    # Download measurement and extract
    ret: Dict[str, Any] = download_file_oss(OSS_ENDPOINT,
                                            OSS_SRC_BUCKET,
                                            OSS_ACCESSKEY,
                                            OSS_SECRETKEY,
                                            object_name,
                                            measurement_filename)
    if ret['status']:
        # Unzip and get measurement name
        with zipfile.ZipFile(measurement_filename) as f:
            f.extractall()
        os.remove(measurement_filename)
        # TODO: There is an agreement that extraction will expand to ./{measurement_name}
        logging.info(f"Got measurement: {measurement_name}")
    else:
        logging.error(f"Error occurs when downloading: \n {ret['error']}")
        return False, object_name, ret

    # When converting measurement, error might occur
    postfix: str = ''
    try:
        convert_measurement(measurement_basedir)
        postfix = 'processed'
    except Exception as err:
        logging.error(f"Error occurs when converting measurement: \n{err}")
        postfix = 'unprocessed'


    # Create zip archive no matter what
    logging.info(f"Creating zip archive")
    archive_filename: str = os.path.join('/tmp', f'{measurement_name}_{postfix}.zip')
    filenames: List[str] = glob.glob(os.path.join(measurement_basedir, '*'))
    with zipfile.ZipFile(archive_filename, 'w', zipfile.ZIP_DEFLATED) as f:
        for filename in filenames:
            f.write(filename, os.path.join(f"{measurement_name}_{postfix}", os.path.basename(filename)))

    # Upload to DST_BUCKET no matter what
    logging.info(f"Uploading to oss")
    try:
        ret: Dict = upload_file_oss(OSS_ENDPOINT, OSS_DST_BUCKET, OSS_ACCESSKEY, OSS_SECRETKEY, archive_filename,
                                    f'{measurement_name}_{postfix}.zip')
    except Exception as err:
        logging.error(f"Exception occurs when uploading: {err}")
        ret = {'status': False}
    logging.info(f"Upload succeeded") if ret['status'] else logging.error(f"Upload failed {ret}")

    # Delete archive and local measurement anyway
    try:
        os.remove(archive_filename)
        shutil.rmtree(measurement_basedir)
    except FileNotFoundError as err:
        logging.warning("File Not Found, the process might not be completed")

    return True, object_name, ret

async def main_loop():
    # Init minio client
    failed_object_names: List[str] = []
    minioClient = Minio(OSS_ENDPOINT, access_key=OSS_ACCESSKEY, secret_key=OSS_SECRETKEY, secure=False) 
    while True:
        objects_list = list(map(lambda x: x.object_name, minioClient.list_objects(OSS_SRC_BUCKET)))
        if len(objects_list) > 0:
            logging.info(f"Got {len(objects_list)} measurements, \n {len(failed_object_names)} failed objects:\n {failed_object_names}")

        # Clean outdated failed objects
        failed_object_names = list(filter(lambda x: x in objects_list, failed_object_names))
        
        # Filter out all failed_objects
        results_list = await asyncio.gather(*[convert(object_name) for object_name in filter(lambda x: x not in failed_object_names, objects_list)])

        # Convert measurements
        for retcode, object_name, _ in results_list:
            if not retcode:
                failed_object_names.append(object_name)
                failed_object_name = f"{object_name.split('.')[0]}_failed.{object_name.split('.')[1]}"
                minioClient.copy_object(bucket_name=OSS_DST_BUCKET, 
                                        object_name=failed_object_name, 
                                        source=f"/{OSS_SRC_BUCKET}/{object_name}")
            
            # Remove old object anyway
            minioClient.remove_object(OSS_SRC_BUCKET, object_name)

        await asyncio.sleep(10)

def init():
    pass


if __name__ == '__main__':
    """
    Constantly monitor oss bucket and convert

    Warning: 
    Files in OSS_SRC_BUCKET might be removed ! OSS_DST_BUCKET and OSS_SRC_BUCKET cannot be same !
    """
    assert OSS_SRC_BUCKET != OSS_DST_BUCKET
    logging.info(f"Start watching buckets: \n > src: {OSS_ENDPOINT}/{OSS_SRC_BUCKET}\n > dst: {OSS_ENDPOINT}/{OSS_DST_BUCKET}\n")
    init()
    asyncio.run(main_loop())