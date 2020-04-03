# ----------------------------------------------------------------------------------------
# Name:        connect_to_cityworks_cwpy.py
# Purpose:     Pass reports from esri to cityworks using the cwpy Cityworks Python Package
# ----------------------------------------------------------------------------------------

from arcgis.gis import GIS  # , Group, Layer
from arcgis.features import FeatureLayer  # , Table
from arcgis.features.managers import AttachmentManager

import cwpy.cwServices
import cwpy.cwMessagesAMS

import requests
import json
from os import path, remove

cw_token = ""
baseUrl = ""
log_to_file = True
global cw_services


def get_response(url, params):
    response = requests.get(url, params=params)
    return json.loads(response.text)

def get_wkid():
    """Retrieve the WKID of the cityworks layers"""
    
    wkid_request = cwpy.cwMessagesAMS.PreferencesService.User()
    wkid_response = cw_services.ams.Preferences_user(wkid_request)

    try:
        return wkid_response["Value"]["SpatialReference"]

    except KeyError:
        return "error"


def get_problem_types():
    """Retrieve a dict of problem types from cityworks"""
    
    problems_requests = cwpy.cwMessagesAMS.ServiceRequestService.Problems()
    problems_requests.ForPublicOnly = True
    problems_response = cw_services.ams.ServiceRequest_problems(problems_requests)

    try:
        values = {}
        for val in problems_response["Value"]:
            values[val["ProblemCode"].upper()] = int(val["ProblemSid"])
        return values

    except Exception as error:
        return "error: " + str(error)


def submit_to_cw(row, prob_types, fields, oid, typefields):

    attrs = row.attributes
    geometry = row.geometry

    try:
        prob_sid = prob_types[attrs[typefields[1]].upper()]

    except KeyError:
        if attrs[typefields[1]].strip() == "":
            return "WARNING: No problem type provided. Record {} not exported.\n".format(oid)
        else:
            return "WARNING: Problem type {} not found in Cityworks. Record {} not exported.\n".format(attrs[typefields[1]], oid)

    except AttributeError:
        return "WARNING: Record {} not exported due to missing value in field {}\n".format(oid, typefields[1])

    # Build dictionary of values to submit to CW
    values = {}
    sr_request = cwpy.cwMessagesAMS.ServiceRequestService.Create()
    for fieldset in fields:
        c_field, a_field = fieldset
        if hasattr(sr_request, c_field):
            setattr(sr_request,c_field,str(attrs[a_field]))
    sr_request.X = geometry["x"]
    sr_request.Y = geometry["y"]
    sr_request.ProblemSid = int(prob_sid)
    
    try:
        sr_response = cw_services.ams.ServiceRequest_create(sr_request)
        return sr_response["Value"]["RequestId"]

    except KeyError:
        return "error"


def copy_attachment(attachmentmgr, attachment, oid, requestid):

    # download attachment
    attpath = attachmentmgr.download(oid, attachment["id"])

    # upload attachment
    file = open(attpath, "rb")
    data = {"RequestId": requestid}
    json_data = json.dumps(data, separators=(",", ":"))
    params = {"token": cw_token, "data": json_data}
    files = {"file": (path.basename(attpath), file)}
    url = "{}/Services/AMS/Attachments/AddRequestAttachment".format(baseUrl)
    response = requests.post(url, files=files, data=params)

    # delete downloaded file
    file.close()
    remove(attpath)

    return json.loads(response.text)


def copy_comments(record, parent, fields, ids):

    values = {ids[0]: parent.attributes[ids[1]]}
    for field in fields:
        values[field[0]] = record.attributes[field[1]]

    json_data = json.dumps(values, separators=(",", ":"))
    params = {"data": json_data, "token": cw_token}
    url = "{}/Services/AMS/CustomerCall/AddToRequest".format(baseUrl)
    response = get_response(url, params)

    return response


def get_parent(lyr, pkey_fld, record, fkey_fld):

    sql = "{} = '{}'".format(pkey_fld, record.attributes[fkey_fld])
    parents = lyr.query(where=sql)
    return parents.features[0]


def main(event, context):

    # Cityworks settings
    global baseUrl
    baseUrl = event["cityworks"]["url"]
    cwUser = event["cityworks"]["username"]
    cwPwd = event["cityworks"]["password"]

    cw_services.url = baseUrl    

    # ArcGIS Online/Portal settings
    orgUrl = event["arcgis"]["url"]
    username = event["arcgis"]["username"]
    password = event["arcgis"]["password"]
    layers = event["arcgis"]["layers"]
    tables = event["arcgis"]["tables"]
    layerfields = event["fields"]["layers"]
    tablefields = event["fields"]["tables"]
    fc_flag = event["flag"]["field"]
    flag_values = [event["flag"]["on"], event["flag"]["off"]]
    ids = event["fields"]["ids"]
    probtypes = event["fields"]["type"]

    if log_to_file:
        from datetime import datetime as dt
        id_log = path.join(sys.path[0], "cityworks_log.log")
        log = open(id_log, "a")
        log.write("\n\n{}\n".format(dt.now()))

    try:
        # Connect to org/portal
        gis = GIS(orgUrl, username, password)

        # Get token for CW
        auth_response = cw_services.authenticate(cwUser, cwPwd)
        if auth_response['Status'] != 0:
            raise Exception("Cityworks not authenticated")

        # get wkid
        sr = get_wkid()

        if sr == "error":
            if log_to_file:
                log.write("Spatial reference not defined\n")
            else:
                print("Spatial reference not defined\n")
            raise Exception("Spatial reference not defined")

        # get problem types
        prob_types = get_problem_types()

        if prob_types == "error":
            if log_to_file:
                log.write("Problem types not defined\n")
            else:
                print("Problem types not defined\n")
            raise Exception("Problem types not defined")

        for layer in layers:
            lyr = FeatureLayer(layer, gis=gis)
            oid_fld = lyr.properties.objectIdField

            # Get related table URL
            reltable = ""
            for relate in lyr.properties.relationships:
                url_pieces = layer.split("/")
                url_pieces[-1] = str(relate["relatedTableId"])
                table_url = "/".join(url_pieces)

                if table_url in tables:
                    reltable = table_url
                    break

            # query reports
            sql = "{}='{}'".format(fc_flag, flag_values[0])
            rows = lyr.query(where=sql, out_sr=sr)
            updated_rows = []

            for row in rows.features:
                oid = row.attributes[oid_fld]

                # Submit feature to the Cityworks database
                requestid = submit_to_cw(row, prob_types, layerfields, oid, probtypes)

                try:
                    if "WARNING" in requestid:
                        if log_to_file:
                            log.write("Warning generated while copying record to Cityworks: {}\n".format(requestid))
                        else:
                            print("Warning generated while copying record to Cityworks: {}\n".format(requestid))
                        continue
                    else:
                        pass  # requestID is str = ok
                except TypeError:
                    pass  # requestID is a number = ok

                # attachments
                attachmentmgr = AttachmentManager(lyr)
                attachments = attachmentmgr.get_list(oid)

                for attachment in attachments:
                    response = copy_attachment(attachmentmgr, attachment, oid, requestid)
                    if response["Status"] is not 0:
                        if log_to_file:
                            log.write("Error while copying attachment to Cityworks: {}\n".format(response["ErrorMessages"]))
                        else:
                            print("Error while copying attachment to Cityworks: {}\n".format(response["ErrorMessages"]))

                # update the record in the service so that it evaluates falsely against sql
                sql = "{}='{}'".format(oid_fld, oid)
                row_orig = lyr.query(where=sql).features[0]
                row_orig.attributes[fc_flag] = flag_values[1]
                try:
                    row_orig.attributes[ids[1]] = requestid
                except TypeError:
                    row_orig.attributes[ids[1]] = str(requestid)

                updated_rows.append(row_orig)

            # apply edits to updated features
            if updated_rows:
                status = lyr.edit_features(updates=updated_rows)
                if log_to_file:
                    log.write("Status of updates to ArcGIS layers: {}\n".format(status))
                else:
                    print("Status of updates to ArcGIS layers: {}\n".format(status))

            
            rel_records = []
            updated_rows = []
                        # related records
            rellyr = FeatureLayer(reltable, gis=gis)
            relname = rellyr.properties['name']

            pkey_fld = lyr.properties.relationships[0]["keyField"]
            fkey_fld = rellyr.properties.relationships[0]["keyField"]
            sql = "{}='{}'".format(fc_flag, flag_values[0])
            rel_records = rellyr.query(where=sql)
            updated_rows = []

            for record in rel_records:
                rel_oid = record.attributes[oid_fld]
                parent = get_parent(lyr, pkey_fld, record, fkey_fld)

                # Upload comment attachments
                try:
                    attachmentmgr = rellyr.attachments
                    attachments = attachmentmgr.get_list(rel_oid)
                    for attachment in attachments:
                        response = copy_attachment(attachmentmgr, attachment, rel_oid, parent.attributes[ids[1]])
                        if response["Status"] is not 0:
                            try:
                                error = response["ErrorMessages"]
                            except KeyError:
                                error = response["Message"]
                            msg = "Error copying attachment. Record {} in table {}: {}".format(rel_oid,
                                                                                                 relname,
                                                                                                 error)
                            if log_to_file:
                                log.write(msg+'\n')
                            else:
                                print(msg)
                except RuntimeError:
                    pass  # table doesn't support attachments

                # Process comments
                response = copy_comments(record, parent, tablefields, ids)

                if 'error' in response:
                    if log_to_file:
                        log.write('Error accessing comment table {}\n'.format(relname))
                    else:
                        print('Error accessing comment table {}'.format(relname))
                    break

                elif response["Status"] is not 0:
                    try:
                        error = response["ErrorMessages"]
                    except KeyError:
                        error = response["Message"]
                    msg = "Error copying record {} from {}: {}".format(rel_oid, relname, error)
                    if log_to_file:
                        log.write(msg+'\n')
                    else:
                        print(msg)
                    continue
                else:
                    record.attributes[fc_flag] = flag_values[1]
                    try:
                        record.attributes[ids[1]] = parent.attributes[ids[1]]
                    except TypeError:
                        record.attributes[ids[1]] = str(parent.attributes[ids[1]])

                    updated_rows.append(record)

            # apply edits to updated records
            if updated_rows:
                status = rellyr.edit_features(updates=updated_rows)
                if log_to_file:
                    log.write("Status of updates to ArcGIS comments: {}\n".format(status))
                else:
                    print("Status of updates to ArcGIS comments: {}\n".format(status))

            print("Finished processing: {}".format(lyr.properties["name"]))

    except Exception as ex:
        print("error: " + str(ex))

    if log_to_file:
        log.close()


if __name__ == "__main__":

    import sys

    configfile = sys.argv[1]  # r"C:\Users\alli6394\Desktop\arcgis_cw_config.ini"

    with open(configfile) as configreader:
        config = json.load(configreader)
    cw_services = cwpy.cwServices.Services()
    main(config, "context")
