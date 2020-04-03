import arcpy
import json
import os

global workspace

def create_fgdb(path,name):
    new_fgdb = arcpy.CreateFileGDB_management(path,name)
    return new_fgdb

def create_gdb_domain(gdb,name,description,ftype,dtype,c_values):
    new_domain = arcpy.CreateDomain_management(in_workspace=gdb,domain_name=name,domain_description=description,field_type=ftype,domain_type=dtype)
    for coded_value in c_values:
        arcpy.AddCodedValueToDomain_management(gdb,name,coded_value,c_values[coded_value])
        
def create_gdb_featureclass(gdb,name):
    fc = arcpy.CreateFeatureclass_management(gdb,name, geometry_type="POINT")
    arcpy.AddGlobalIDs_management(fc)
    arcpy.EnableAttachments_management(fc)
    arcpy.EnableEditorTracking_management(fc, "created_user","created_date","last_edit_user","last_edit_date","ADD_FIELDS","UTC")


def add_gdb_field(path,gdb_name,fc_key,fc,field_dict, domains_dict):
    field_name_lower = field_dict['field_name'].lower()
    arcpy.env.workspace = path + '/' + gdb_name
    if field_dict['field_domain'] != None:
        if field_dict['field_domain'] == "FIELDKEY":
            field_domain = fc_key
            arcpy.AddField_management(fc,field_name=field_name_lower,field_type=field_dict['field_type'],field_length=field_dict['field_length'],
                                          field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_domain)                                

        else:
            if field_dict['default_value'] != None:
                arcpy.AddField_management(fc,field_name=field_name_lower,field_type=field_dict['field_type'],
                                          field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_dict['field_domain'])
                arcpy.AssignDefaultToField_management(in_table=fc,field_name=field_name_lower,default_value=field_dict['default_value'])
            else:
                arcpy.AddField_management(fc,field_name=field_name_lower,field_type=field_dict['field_type'],
                                                      field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_dict['field_domain'])                
                
    else:
        arcpy.AddField_management(fc,field_name=field_name_lower,field_type=field_dict['field_type'],
                                      field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'])

    print("Field {} added to Feature Class {}".format(field_dict['field_name'],fc))
    
def get_dict(json_file):
    data = json.load(open(json_file))
    return data
    
    
if __name__ == "__main__":
    arcpy.env.overwriteOutput = True
    gdb_path = os.path.dirname(os.path.realpath(__file__))
    workspace = gdb_path
    arcpy.env.workspace = workspace
    gdb_name = "CrowdsourceProblemTypes.gdb"
    domain_json = "gdb_domains.json"
    gdb = create_fgdb(gdb_path,gdb_name)
    gdb_domains = get_dict(domain_json)
    for domain in gdb_domains['Domains']:
        create_gdb_domain(gdb,domain['Name'],domain['Description'],domain['Field Type'],domain['Domain Type'],domain['Coded Values'])
    fc_json = "gdb_featureclasses.json"
    gdb_fcs = get_dict(fc_json)
    field_json = "gdb_featureclass_fields.json"
    gdb_fields = get_dict(field_json)    
    for fc in gdb_fcs['FeatureClasses']:
        create_gdb_featureclass(gdb,gdb_fcs['FeatureClasses'][fc])
        for field_schema in gdb_fields['Fields']:
            add_gdb_field(gdb_path,gdb_name,fc,gdb_fcs['FeatureClasses'][fc],field_schema, gdb_domains['Domains'])        
        
        
