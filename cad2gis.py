#!/usr/bin/env python3

import logging
import fiona
import geopandas
import pandas
import shapely
import json
import os
import pathlib
import shutil
import subprocess
import sys
import traceback
import uuid
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename
import time
import math

logger = logging.getLogger('autocad-to-gis')
logger.setLevel(logging.DEBUG)
logging.basicConfig(filename='log/cad2gis.log', filemode='w')
# logger.info('start logger')

# #!/bin/bash

# set -e
# set -x

# rm -rf /tmp/.X99-lock
# Xvfb :99 -screen 0 1024x768x16 &
# while [ ! -e /tmp/.X11-unix/X99 ]; do sleep 0.1; done

# export DXF_ENCODING=UTF-8
# export XDG_RUNTIME_DIR='/tmp/runtime-root'

# for folder in $(find /data -type f -name "*.dwg" -exec dirname {} \; | sort -u); do
#     DISPLAY=:99.0 ODAFileConverter \
#         "${folder}" \
#         "${folder}" \
#         ACAD2018 DXF 1 1 "*.dwg"
#         # ACAD2015 DXF 1 1 "*.dwg"
#         # ACAD2000 DXF 1 1 "*.dwg"
#         # ACAD2014 DXF 1 1 "*.dwg"
#         # ACAD12 DXF 1 1 "*.dwg"
#         # ACAD2010 DXF 1 1 "*.dwg"
# done

# echo "finished !"

UPLOAD_FOLDER = '/data'
ALLOWED_EXTENSIONS = {'dwg', 'dxf'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 40 * 1000 * 1000
socketio = SocketIO(
    app,
    logger=True,
    engineio_logger=True,
    cors_allowed_origins="*")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_setup(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'json'}

# wget http://localhost:9090/data/8fa47945beae4b56af301f0b9e0a3dcf.dwg
# @app.route('/api/cad2gis/data/<name>')
# def download_file(name):
    # return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/api/cad2gis/get_geojson/<file_id>', methods=['GET'])
def get_geojson(file_id):
    return send_from_directory(app.config["UPLOAD_FOLDER"], file_id, "geojson", "plan.geojson")

@app.route('/api/cad2gis/wait_geojson/<file_id>', methods=['GET'])
def wait_geojson(file_id):
    file_path=os.path.join(app.config["UPLOAD_FOLDER"], file_id, "geojson", "plan.geojson")
    status = 400
    message = "isn't a file"
    while not os.exists(file_path):
        time.sleep(1)
    if os.path.isfile(file_path):
        status = 200
        message = "file ready"
    return app.response_class(
        response=json.dumps(
            {"message": message}
        ),
        status=status,
        mimetype='application/json'
    )

# curl -F "file=@autocad-to-gis/data/kingconf/sett_22-11_14.dxf" \
#     https://autocad-to-geojson.openindoor.io/api/cad2gis/convert/-0.8782/47.0545/0.0/0.0/45.0/0.5
@app.route('/api/cad2gis/convert/<float(signed=True):lng>/<float(signed=True):lat>/<float(signed=True):xoff>/<float(signed=True):yoff>/<float(signed=True):rot>/<float(signed=True):scale>', methods=['POST'])
@app.route('/api/cad2gis/convert/<float(signed=True):lng>/<float(signed=True):lat>/<float(signed=True):xoff>/<float(signed=True):yoff>/<float(signed=True):rot>', methods=['POST'])
@app.route('/api/cad2gis/convert/<float(signed=True):lng>/<float(signed=True):lat>/<float(signed=True):xoff>/<float(signed=True):yoff>', methods=['POST'])
@app.route('/api/cad2gis/convert/<float(signed=True):lng>/<float(signed=True):lat>', methods=['POST'])
def convert_all(lng, lat, xoff = 0.0, yoff = 0.0, rot = 0.0, scale = 1.0):
    return convert_all_(lng, lat, xoff, yoff, rot, scale)



def convert_all_(lng, lat, xoff = 0.0, yoff = 0.0, rot = 0.0, scale = 1.0):
    filename = "plan.dwg"
    
    file_base = os.path.splitext(filename)[0]
    file_ext = os.path.splitext(filename)[1]
    file_uuid = uuid.uuid4().hex

    # AutoCAD file
    autocad_folder = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file_uuid,
        "autocad",
    )
    pathlib.Path(autocad_folder).mkdir(parents=True, exist_ok=True)
    autocad_path = os.path.join(
        autocad_folder,
        filename
    )
    logger.debug('Original file: %s', autocad_path)

    # ASCII DXF
    ascii_dxf_folder = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file_uuid,
        "ascii_dxf",
    )
    pathlib.Path(ascii_dxf_folder).mkdir(parents=True, exist_ok=True)
    ascii_dxf_path = os.path.join(
        ascii_dxf_folder,
        file_base + ".dxf"
    )
    logger.debug('DXF ASCII file: %s', ascii_dxf_path)

    # geojson file
    geojson_folder = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file_uuid,
        "geojson",
    )
    pathlib.Path(geojson_folder).mkdir(parents=True, exist_ok=True)
    geojson_path = os.path.join(
        geojson_folder,
        file_base + ".geojson"
    )
    logger.debug('Geojson to write: %s', geojson_path)

    with open(autocad_path, "bw") as f:
        chunk_size = 4096
        while True:
            chunk = request.stream.read(chunk_size)
            if len(chunk) == 0:
                break
            f.write(chunk)

    # send("file received")

    # file.save(autocad_path)

    # Get setup as a file
    setup = None
    my_setup = {}
    if 'setup' not in request.files:
        logger.debug('No setup file')
        # flash('No setup part')
    else:
        setup = request.files['setup']
        if setup.filename == '':
            logger.debug('No setup file')
        if not (setup and allowed_setup(setup.filename)):
            setup = None
    if setup is not None:
        logger.info('setup.filename: %s', setup.filename)
        setup_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            file_uuid,
            "setup.json",
        )
        setup.save(setup_path)
        with open(setup_path, 'r') as f:
            my_setup = json.load(f)
    if "scale" in my_setup:
        scale = my_setup['scale']
    if "rotation" in my_setup:
        rot = my_setup['rotation']
    if "longitude" in my_setup:
        lng = my_setup['longitude']
    if "latitude" in my_setup:
        lat = my_setup['latitude']
    # Convert Autocad data to ASCII DXF
    print('autocad_path:', autocad_path, file=sys.stderr, flush=True)
    cmd = [
        "/openindoor/autocad-to-ascii_dxf.sh",
        autocad_folder,
        ascii_dxf_folder,
    ]
    print(cmd, file=sys.stderr, flush=True)
    logger.info('cmd: %s', cmd)
    print('Process AutoCAD to ASCII dxf conversion...', end='', file=sys.stderr, flush=True)
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
    )
    print('OK !', file=sys.stderr, flush=True)

        # shell=True,
        # capture_output=True,
        # text=True,
        # stdout=subprocess.PIPE,
        # env={
        #     "DXF_ENCODING": "UTF-8",
        #     "XDG_RUNTIME_DIR": "/tmp/runtime-root",
        #     "DISPLAY": ":99.0",
        # }
    # )

    ogrinfo = subprocess.run(
        [
            "ogrinfo",
            "-ro",
            ascii_dxf_path
        ],
        stdout = subprocess.PIPE,
        env={"DXF_FEATURE_LIMIT_PER_BLOCK": "-1"}
    )
    print('ogrinfo:', ogrinfo, file=sys.stderr, flush=True)
    logger.info('ogrinfo: %s', ogrinfo)

    # print(result.stderr, file=sys.stderr)
    if (result.returncode != 0):
        print("returncode:", result.returncode, file=sys.stderr, flush=True)
        return app.response_class(
            response=json.dumps(
                {"returncode": result.returncode}
            ),
            status=400,
            mimetype='application/json'
        )
    # print(result.stderr, file=sys.stderr)

    # Convert ASCII DXF file to geojson

    # lambert_93 = "EPSG:27561"
# https://gdal.org/drivers/vector/dxf.html
# GDAL writes DXF files with measurement units set to “Imperial - Inches”. If you need to change the units, edit the $MEASUREMENT and $INSUNITS variables in the header template.
    crs = "+proj=lcc" \
    " +lat_1=" + str(lat) + "" \
    " +lat_0=" + str(lat) + "" \
    " +lon_0=" + str(lng) + "" \
    " +k_0=0.999877341" \
    " +a=6378249.2" \
    " +b=6356515" \
    " +units=m" \
    " +no_defs"

    # " +towgs84=-168,-60,320,0,0,0,0" \
    # " +pm=paris" \
    # " +x_0=600000" \
    # " +y_0=200000" \

    print("crs:", crs, file=sys.stderr)

    # crs = '+proj=lcc +lat_1=' + str(lat) + ' +units=m +no_defs'
    try:
        # ascii_dxf = geopandas.read_file(
        #     ascii_dxf_path,
        #     encoding='utf-8',
        #     env = fiona.Env(DXF_ENCODING="UTF-8")
        # )

        print('Importing collection 1/2...', end='', file=sys.stderr, flush=True)
        collection = list(fiona.open(ascii_dxf_path,'r'))
        print('OK !', file=sys.stderr, flush=True)

        print('Importing collection 2/2...', end='', file=sys.stderr, flush=True)
        df1 = pandas.DataFrame(collection)
        print('OK !', file=sys.stderr, flush=True)

        #Check Geometry
        def isvalid(geom):
            try:
                shapely.geometry.shape(geom)
                return 1
            except:
                return 0
        df1['isvalid'] = df1['geometry'].apply(lambda x: isvalid(x))
        df1 = df1[df1['isvalid'] == 1]
        collection = json.loads(df1.to_json(orient='records'))

        #Convert to geodataframe
        ascii_dxf = geopandas.GeoDataFrame.from_features(collection)

        # logger.debug('ascii_dxf: %s', ascii_dxf)
        print('ascii_dxf.crs:', ascii_dxf.crs, file=sys.stderr)
        ascii_dxf.set_crs(
            crs = crs,
            inplace = True
        )
        print('ascii_dxf.crs:', ascii_dxf.crs, file=sys.stderr, flush=True)
        logger.info('Applied crs: %s', ascii_dxf.crs)

        # total_bounds = ascii_dxf.total_bounds
        # print('total_bounds:', total_bounds, file=sys.stderr)
        # print('total_bounds[0]:', total_bounds[0], file=sys.stderr)

        print('calculate total bounds...', end='', file=sys.stderr, flush=True)
        total_bounds = ascii_dxf.total_bounds
        print('OK !', file=sys.stderr, flush=True)

        # Add a bounding box
        # bbox_geom = shapely.geometry.box(*total_bounds)
        # # logger.debug('total_bounds arguments: %s', total_bounds)
        # logger.debug('bbox geometry: %s', bbox_geom)
        # my_bb = geopandas.GeoDataFrame({
        #     'Layer': ['bounding_box'],
        #     'geometry': [bbox_geom]
        # })
        # ascii_dxf = geopandas.GeoDataFrame( pandas.concat( (ascii_dxf, my_bb), ignore_index=True) )

        print('Process rotation ' + str(rot) + ' ...', end='', file=sys.stderr, flush=True)
        if (not math.isclose(rot, 0.0)):
            ascii_dxf['geometry'] = ascii_dxf.rotate(
                angle = rot,
                origin=(
                    (total_bounds[2] + total_bounds[0]) / 2,
                    (total_bounds[3] + total_bounds[1]) / 2
                )
            )
            print('Done !', file=sys.stderr, flush=True)
        else:
            print('Nothing to do !', file=sys.stderr, flush=True)
        # logger.debug('ascii_dxf rotated: %s', ascii_dxf)

        logger.debug('total_bounds: %s', total_bounds)

        print('Process scaling ' + str(scale) + " ...", end='', file=sys.stderr, flush=True)
        if (not math.isclose(scale, 1.0)):
            ascii_dxf['geometry'] = ascii_dxf.scale(
                xfact=scale,
                yfact=scale,
                zfact=scale,
                origin=(
                    (total_bounds[2] + total_bounds[0]) / 2,
                    (total_bounds[3] + total_bounds[1]) / 2
                )
            )
            print('Done !', file=sys.stderr, flush=True)
        else:
            print('Nothing to do !', file=sys.stderr, flush=True)
        # logger.debug('ascii_dxf scaled: %s', ascii_dxf)

        # print('total_bounds 2:', total_bounds, file=sys.stderr)

        print('Process EPSG:4326...', end='', file=sys.stderr, flush=True)
        my_epsg = ascii_dxf.to_crs('EPSG:4326')
        print('OK !', file=sys.stderr, flush=True)
        # logger.debug('my_epsg to_crs: %s', my_epsg)

        # my_lcc_geojson = ascii_dxf.to_json()

        # total_bounds = my_epsg.total_bounds
        print('Process translation (' + str(xoff) + ', ' + str(yoff) + ', 0.0) ...', end='', file=sys.stderr, flush=True)
        logger.info('Apply offsets: xoff:%s yoff:%s', xoff, yoff)
        if not (math.isclose(xoff, 0.0) and math.isclose(yoff, 0.0)):
            my_epsg['geometry'] = my_epsg.translate(
                xoff=xoff,
                yoff=yoff,
                zoff=0.0
            )
            print('Done !', file=sys.stderr, flush=True)
        else:
            print('Nothing to do !', file=sys.stderr, flush=True)

        # Start file_content twist
        if ("transforms" in my_setup):
            for transform in my_setup["transforms"]:
                logger.debug('transform: %s', transform)
                if ("rules" in transform):
                    my_sub_epsg = my_epsg
                    for rule in transform["rules"]:
                        logger.debug('rule: %s', rule)
                        value = transform["rules"][rule]
                        logger.debug('value: %s', value)
                        my_sub_epsg = my_sub_epsg[my_sub_epsg[rule]==value]
                        logger.debug('my_sub_epsg: %s', my_sub_epsg)
                    
                    my_sub_epsg = my_sub_epsg.apply(
                        lambda row: alter_row(row, transform),
                        axis=1,
                        result_type='expand'
                    )

                    my_epsg = my_epsg.merge(my_sub_epsg, how='left')

        print('Convert to geojson...', end='', file=sys.stderr, flush=True)
        my_geojson = my_epsg.to_json(na = 'drop')
        final_geojson = json.loads(my_geojson)
        final_geojson["@context"] =  {
            "id": file_uuid,
        }
        print('OK !', file=sys.stderr, flush=True)

        print('geojson_path:', geojson_path, file=sys.stderr)
        logger.info('geojson generated here: %s', geojson_path)
        my_geojson = json.dumps(final_geojson)
        # my_epsg.to_file(geojson_path, driver='GeoJSON')  
        with open(geojson_path, 'w') as f:
            f.write(my_geojson)

        # print("geojson:", my_geojson, file=sys.stderr)
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)

    
    # cmd = [
    #     "ogr2ogr", "-f", "GeoJSON",
    #     # "/vsistdin/",
    #     "/vsistdout/",
    #     # geojson_path,
    #     ascii_dxf_path,
    # ]
    # print("cmd:", cmd, file=sys.stderr)

    # my_exec = subprocess.run(
    #     cmd,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     env={
    #         "DXF_ENCODING": "UTF-8",
    #     }
    # )
    # print(my_exec.stdout, file=sys.stderr)
    # print(my_exec.stderr, file=sys.stderr)
    # my_geojson = json.loads(my_exec.stdout)

    print('Return result !', end='', file=sys.stderr, flush=True)
    return app.response_class(
        response=my_geojson,
        status=200,
        mimetype='application/json'
    )

    # print('calculate_content_length():', response.calculate_content_length(), file=sys.stderr, flush=True)
    # return response


def alter_row(row, transform):
    if ("properties" in transform):
        for property in transform["properties"]:
            value = transform["properties"][property]
            if value.startswith('$'):
                value = row[value[1:]]
            # logger.debug('value: %s', value)
            row[property] = value
        # logger.debug('row: %s', row)
    return row

# # wget http://localhost:9090/data/8fa47945beae4b56af301f0b9e0a3dcf.dwg
# @app.route('/data/<name>')
# def download_file(name):
#     return send_from_directory(app.config["UPLOAD_FOLDER"], name)

app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)

# curl http://localhost:9090/api/dwg-to-dxf/8fa47945beae4b56af301f0b9e0a3dcf
@app.route("/api/dwg-to-dxf/<string:file_id>")
def dwg_to_dxf(file_id):
    dest_dir = "/tmp/dwg_" + file_id
    tmp_dwg = dest_dir + "/my.dwg"
    pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)
    shutil.copy2("/data/" + file_id + ".dwg", tmp_dwg)
# DISPLAY=:99.0 ODAFileConverter \
#     /tmp/dwg_8fa47945beae4b56af301f0b9e0a3dcf \
#     /tmp/dwg_8fa47945beae4b56af301f0b9e0a3dcf \
#     ACAD2018 DXF 1 1 "*.dwg"
    cmd = [
        "ODAFileConverter",
        dest_dir,
        dest_dir,
        "ACAD2018", "DXF", "1", "1", '"*.dwg"'
    ]
    logger.info('cmd: %s', cmd)

    cmd = ["env"]
    subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )

    response = app.response_class(
        status=200,
    )
    return response

@socketio.on('autocad_file')
def on_autocad_file(data):
    print('------------- coucou', file=sys.stderr, flush=True)
    os._exit(1)
# @socketio.on('my event')
# def handle_my_custom_event(json):
#     print('received json: ' + str(json), file=sys.stderr, flush=True)

@socketio.on('my event')
def handle_my_custom_event(json):
    print('------------- received json: ' + str(json), file=sys.stderr, flush=True)

if __name__ == '__main__':
    # app.run(port=5000, debug=True, host="0.0.0.0")
    socketio.run(app, port=5000, debug=True, host="0.0.0.0")




