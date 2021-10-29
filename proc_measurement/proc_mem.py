"""proc_mem.py"""
from typing import Dict
import os
import zipfile
import json
import logging
import glob
import shutil

from flask import Flask, request, Response
from gevent import pywsgi

from helpers import get_mem_from_url, convert_measurement, upload_file_oss

# from credentials import OSS_ENDPOINT, OSS_BUCKET, OSS_ACCESSKEY, OSS_SECRETKEY

OSS_ENDPOINT = os.environ['OSS_ENDPOINT']
OSS_BUCKET = os.environ['OSS_BUCKET']
OSS_ACCESSKEY = os.environ['OSS_ACCESSKEY']
OSS_SECRETKEY = os.environ['OSS_SECRETKEY']
DEGUG:bool = bool(os.environ['DEBUG']) if 'DEBUG' in os.environ.keys() else False

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route("/run", methods=['GET', 'POST'])
def run():
    resp = Response(mimetype='application/json')

    try:
        params = request.get_json()["value"]  # extract real arguments
        logging.info(f"Got parameters: \n{params}")
    except KeyError:
        logging.error("No argument")
        resp.status = 500
        resp.data = json.dumps({"code": 500, "msg": "No argument"})
        return resp
    try:
        url = params['url']
        object_name = params['object_name']
        bucket_name = params['bucket_name']
    except KeyError:
        print("[ Error ] Wrong parameters")
        resp = Response(status=500)
        resp.data = json.dumps({"code": 500, "msg": "Wrong parameters"})
        return resp

    # Download measurement and extract
    measurement_name = get_mem_from_url(url, object_name)
    logging.info(f"Sucessfully got measurement: {measurement_name}")
    measurement_basedir = os.path.join('.', measurement_name)

    # When converting measurement, error might occur
    postfix: str = ''
    try:
        convert_measurement(measurement_basedir)
        postfix = 'processed'
    except Exception as err:
        logging.error(f"Error occurs when converting measurement: \n{err}")
        postfix = 'unprocessed'

    # Create zip archive
    logging.info(f"Creating zip archive")
    archive_filename = os.path.join('/tmp', f'{measurement_name}_{postfix}.zip')
    filenames = glob.glob(os.path.join(measurement_basedir, '*'))
    with zipfile.ZipFile(archive_filename, 'w', zipfile.ZIP_DEFLATED) as f:
        for filename in filenames:
            f.write(filename, os.path.join(f"{measurement_name}_{postfix}", os.path.basename(filename)))

    # Upload to Object Storage
    logging.info(f"Uploading to oss")
    try:
        ret: Dict = upload_file_oss(OSS_ENDPOINT, OSS_BUCKET, OSS_ACCESSKEY, OSS_SECRETKEY, archive_filename,
                                    f'{measurement_name}_{postfix}.zip')
    except Exception as err:
        logging.error(f"Exception occurs when uploading: {err}")
        ret = {'status': False}
    os.remove(archive_filename)
    shutil.rmtree(measurement_basedir)

    resp.status = 200 if ret['status'] else 500
    resp.data = json.dumps({"code": resp.status}) if ret['status'] else json.dumps({"code": resp.status, "info": str(err)})
    return resp


@app.route("/init", methods=['GET', 'POST'])
def init():
    resp = Response(mimetype='application/json')
    resp.status = 200
    resp.data = json.dumps({"code": 200})
    return resp


if __name__ == '__main__':

    SERVING_PORT: int = 18880
    init()
    if DEGUG:
        app.run('0.0.0.0', SERVING_PORT)
    else:
        server = pywsgi.WSGIServer(('0.0.0.0', SERVING_PORT), app)
        server.serve_forever()