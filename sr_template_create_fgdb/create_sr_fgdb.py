import arcpy
import json
import os
import requests

global workspace

base_url = ""
cw_token = ""

def add_gdb_field(path,gdb_name,fc,field_dict):
    arcpy.env.workspace = path + '/' + gdb_name
    if field_dict['field_domain'] != None:
        if field_dict['default_value'] != None:
            arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_dict['field_domain'])
            arcpy.AssignDefaultToField_management(in_table=fc,field_name=field_dict['field_name'],default_value=field_dict['default_value'])
        else:
            arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_dict['field_domain'])                
                
    else:
        if field_dict['field_type'] == "TEXT":
            arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'])
        elif field_dict['field_type'] == "LONG":
            arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],field_precision=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'])
        else:
            arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'])

def create_relationship_class(gdb_name,orig,dest, orig_name, dest_name):
    #origin_table = "{}/{}".format(gdb_name,orig)
    #dest_table = "{}/{}".format(gdb_name,dest)
    rel_class = "{}/{}_has_{}".format(gdb_name,orig_name,dest_name)
    arcpy.CreateRelationshipClass_management(origin_table=orig,destination_table=dest,out_relationship_class=rel_class,
                                             relationship_type="COMPOSITE",forward_label=dest_name,backward_label=orig_name,message_direction="NONE",cardinality="ONE_TO_MANY",attributed=False,origin_primary_key="GlobalID",
                                             origin_foreign_key="parentglobalid")

def get_response(url, params):
    try:
        response = requests.get(url, params=params)
        return json.loads(response.text)
    except:
        print("JSON not returned, check errors.axd")
        return {}
    
def get_dict(workspace,json_file):
    data = json.load(open(workspace+"\\"+json_file))
    return data

def format_data(data_dict):
    token = cw_token
    json_data = json.dumps(data_dict, separators=(",",":"))
    if len(list(token)) == 0:
        params = {"data":json_data}
    else:    
        params = {"token": token, "data": json_data}
    
    return params

def get_cw_token(user, pwd):
    #Retrieve a token for Cityworks access
    data = {"LoginName": user, "Password": pwd}
    params = format_data(data)
    url = "{}/Services/Authentication/Authenticate".format(base_url)

    response = get_response(url, params)

    if response['Status'] is not 0:
        return "error: {}: {}".format(response['Status'],
                                      response['Message'])
    else:
        global cw_token
        cw_token = response['Value']['Token']
        return "success"
    
def create_fgdb(path,name):
    new_fgdb = arcpy.CreateFileGDB_management(path,name)
    print("File Geodatabase {} created".format(name))
    return new_fgdb
    
def get_sr_templates():
    data = {"ForPublicOnly":True}
    params = format_data(data)
    url = "{}/Services/AMS/ServiceRequest/Problems".format(base_url)
    try:
        sr_temp_response = get_response(url, params)
        if sr_temp_response['Value'] != None:
            return sr_temp_response['Value']
        else:
            print(sr_temp_response)
    
    except Exception as e:
        print(e)
        return None
    
def exit_on_error():
    input("Press Enter to close")
    exit()
    
def choose_sr_templates(sr_templates):
    print("Service Request templates:")
    for x in range(0, len(sr_templates)):
        print("{}: {}".format(x, sr_templates[x]['Description']))    
    skip_int = int(input("How many Service Request templates would you like to configure? (Enter an integer): "))
    if skip_int == 0:
        exit_on_error()
    print("Which Service Request template(s) would you like to configure?")    
    chosen_matches = []
    try:
        for x in range(skip_int):        
            sr_choice_int = int(input("Enter the corresponding number and press Enter: "))
            chosen_matches.append(sr_templates[sr_choice_int])
        #for testing
        #survey_choice_int = 0
    except Exception as e:
        print(e)
        exit_on_error()
        
    return chosen_matches

def get_sr_temps(prob_sids):
    data = {}
    data['ProblemSids']=prob_sids
    params = format_data(data)
    url = "{}/Services/AMS/ServiceRequestTemplate/ByIds".format(base_url)
    try:
        sr_templates_response = get_response(url, params)
        if sr_templates_response['Value'] != None:
            return sr_templates_response['Value']
        else:
            return []

    except Exception as e:
        print(e)
        return None
    
def create_problem_field_domain(gdb, sr_temps, field_type):
    #sr_temps is list of ProblemLeafBase 
    dtype = "CODED"
    gdb_domain_name = "ProblemTypes"
    #Dictionary to hold coded domain values
    c_values = {}
    for sr_temp in sr_temps:
        #c_values will look like {"SNOW":"Plow Snow"}
        c_values[sr_temp['ProblemCode']] = sr_temp['Description']
    #Create Field Domain for Service Request Templates
    create_gdb_domain(gdb, gdb_domain_name, "Problem Types", field_type, dtype, c_values)
    
def create_gdb_table(gdb,name):
    gdb_table = arcpy.CreateTable_management(gdb,name)
    print("Table {} created".format(name))
    return gdb_table

def create_gdb_featureclass(gdb,name):
    fc = arcpy.CreateFeatureclass_management(gdb,name, geometry_type="POINT")
    arcpy.EnableAttachments_management(fc)
    arcpy.AddGlobalIDs_management(fc)
    arcpy.EnableEditorTracking_management(fc, creator_field = "created_user", creation_date_field = "created_date", last_editor_field = "last_edit_user", 
                                          last_edit_date_field = "last_edit_date",add_fields = True,record_dates_in ="UTC")
    print("Feature Class {} created".format(name))
    #Add comments table
    fc_comments_name = "{}_Comments".format(name)
    fc_comments = create_gdb_table(gdb,fc_comments_name)
    arcpy.EnableAttachments_management(fc_comments)
    arcpy.AddGlobalIDs_management(fc_comments)
    arcpy.EnableEditorTracking_management(fc_comments, creator_field = "created_user",creation_date_field = "created_date",last_editor_field = "last_edit_user",last_edit_date_field = "last_edit_date",add_fields = True,record_dates_in = "UTC")    
    return fc, fc_comments, fc_comments_name


def add_other_fields(gdb_path, gdb_name, gdb, fc_name):
    pass
    
#problem_temps is a list of ProblemName object
def transform(problem_temps):
    #Create ArcPy environment
    arcpy.env.overwriteOutput = True
    sr = arcpy.SpatialReference(3857)
    arcpy.env.outputCoordinateSystem = sr
    gdb_path = os.path.dirname(os.path.realpath(__file__))
    workspace = gdb_path
    arcpy.env.workspace = workspace
    gdb_name = "{}_{}".format("ServiceRequest","ProblemTypes")
    #Create File Geodatabase
    gdb = create_fgdb(gdb_path,gdb_name)
    #Create Point Feature Class for submissions
    fc_name = "Submissions"
    fc, fc_comment, fc_comments_name = create_gdb_featureclass(gdb, fc_name)
    #Get ProblemLeaveBase objects
    prob_sids = []
    for prob in problem_temps:
        prob_sids.append(prob['ProblemSid'])
    sr_temps= get_sr_temps(prob_sids)
    #Create ProblemType Domain
    if len(sr_temps) > 0:
        #List of ProblemLeafBase objects
        field_type = "TEXT"
        create_problem_field_domain(gdb, sr_temps, field_type)
    #Status and Yes/No domains
    gdb_acc_domains = get_dict(workspace,"gdb_acc_domains.json")
    for acc_domain in gdb_acc_domains['Domains']:
        create_gdb_domain(gdb,acc_domain['Name'],acc_domain['Description'],acc_domain['Field Type'],acc_domain['Domain Type'],acc_domain['Coded Values'])
    fc_field_json = "gdb_featureclass_fields.json"
    gdb_fields = get_dict(workspace,fc_field_json)
    tbl_field_json = "gdb_comments_fields.json"
    tbl_fields = get_dict(workspace,tbl_field_json)
    for field_schema in gdb_fields['Fields']:
        add_gdb_field(gdb_path,gdb_name,fc,field_schema)
    for field_schema in tbl_fields['Fields']:
        add_gdb_field(gdb_path,gdb_name,fc_comment,field_schema)
    create_relationship_class(gdb_name,fc,fc_comment, fc_name, fc_comments_name)    
        
def create_gdb_domain(gdb,name,description,ftype,dtype,c_values):
    new_domain = arcpy.CreateDomain_management(in_workspace=gdb,domain_name=name,domain_description=description,field_type=ftype,domain_type=dtype)
    for coded_value in c_values:
        arcpy.AddCodedValueToDomain_management(gdb,name,coded_value,c_values[coded_value])
    print("Field Domain {} added to FGDB".format(name))
    

def main(event, context):
    #Cityworks settings
    global base_url
    base_url = event['CityworksURL']
    cw_user = event['CityworksUsername']
    cw_password = event['CityworksPassword']
    
    #Authenticate Cityworks
    cw_status = get_cw_token(cw_user, cw_password)
    if "error" in cw_status:
        raise ValueError("Error Authenticating Cityworks")    
    
    sr_templates = get_sr_templates()
    if sr_templates != None:
        chosen_templates = choose_sr_templates(sr_templates)
        transform(chosen_templates)
        
    else:
        exit_on_error()

if __name__ == "__main__":
    import sys
    
    configfile = sys.argv[1]  # config.json
    
    with open(configfile) as configreader:
        config = json.load(configreader)    
    
    main(config,"context")