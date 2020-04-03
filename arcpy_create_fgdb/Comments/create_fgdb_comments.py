import arcpy
import json
import os

global workspace

def create_fgdb(path,name):
    new_fgdb = arcpy.CreateFileGDB_management(path,name)
    print("File Geodatabase {} created".format(name))
    return new_fgdb

def create_gdb_domain(gdb,name,description,ftype,dtype,c_values):
    new_domain = arcpy.CreateDomain_management(in_workspace=gdb,domain_name=name,domain_description=description,field_type=ftype,domain_type=dtype)
    for coded_value in c_values:
        arcpy.AddCodedValueToDomain_management(gdb,name,coded_value,c_values[coded_value])
    print("Field Domain {} added to FGDB".format(name))
        
def create_gdb_featureclass(gdb,name):
    fc = arcpy.CreateFeatureclass_management(gdb,name, geometry_type="POINT")
    arcpy.AddGlobalIDs_management(fc)
    arcpy.EnableAttachments_management(fc)
    arcpy.EnableEditorTracking_management(fc, "created_user","created_date","last_edit_user","last_edit_date","ADD_FIELDS","UTC")
    print("Feature Class {} created".format(name))
    #Add comments table
    fc_comments_name = "{}_Comments".format(name)
    fc_comments = create_gdb_table(gdb,fc_comments_name)
    arcpy.AddGlobalIDs_management(fc_comments)
    arcpy.EnableAttachments_management(fc_comments)    
    arcpy.EnableEditorTracking_management(fc_comments, "created_user","created_date","last_edit_user","last_edit_date","ADD_FIELDS","UTC")
    return fc_comments_name
    
def create_gdb_table(gdb,name):
    gdb_table = arcpy.CreateTable_management(gdb,name)
    print("Table {} created".format(name))
    return gdb_table

def create_relationship_class(gdb_name,orig,dest):
    origin_table = "{}/{}".format(gdb_name,orig)
    dest_table = "{}/{}".format(gdb_name,dest)
    rel_class = "{}/{}_has_{}".format(gdb_name,orig,dest)
    arcpy.CreateRelationshipClass_management(origin_table=origin_table,destination_table=dest_table,out_relationship_class=rel_class,
                                             relationship_type="COMPOSITE",forward_label=dest,backward_label=orig,message_direction="NONE",cardinality="ONE_TO_MANY",attributed=False,origin_primary_key="GlobalID",
                                             origin_foreign_key="parentglobalid")


def add_gdb_field(path,gdb_name,fc_key,fc,field_dict, domains_dict):
    arcpy.env.workspace = path + '/' + gdb_name
    if field_dict['field_domain'] != None:
        if field_dict['field_domain'] == "FIELDKEY":
            field_domain = fc_key
            arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],field_length=field_dict['field_length'],
                                          field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_domain)                                

        else:
            if field_dict['default_value'] != None:
                arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],
                                          field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_dict['field_domain'])
                arcpy.AssignDefaultToField_management(in_table=fc,field_name=field_dict['field_name'],default_value=field_dict['default_value'])
            else:
                arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],
                                                      field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'],field_domain=field_dict['field_domain'])                
                
    else:
        arcpy.AddField_management(fc,field_name=field_dict['field_name'],field_type=field_dict['field_type'],
                                      field_length=field_dict['field_length'],field_alias=field_dict['field_alias'],field_is_nullable=field_dict['field_is_nullable'])

    print("Field {} added to Feature Class {}".format(field_dict['field_name'],fc))
    
    
def get_dict(workspace,json_file):
    data = json.load(open(workspace+"\\"+json_file))
    return data
    
    
if __name__ == "__main__":
    arcpy.env.overwriteOutput = True
    sr = arcpy.SpatialReference(3857)
    arcpy.env.outputCoordinateSystem = sr
    gdb_path = os.path.dirname(os.path.realpath(__file__))
    workspace = gdb_path
    arcpy.env.workspace = workspace
    gdb_name = "crowdsource_w_comments.gdb"
    domain_json = "gdb_domains.json"
    gdb = create_fgdb(gdb_path,gdb_name)
    gdb_domains = get_dict(workspace,domain_json)
    for domain in gdb_domains['Domains']:
        create_gdb_domain(gdb,domain['Name'],domain['Description'],domain['Field Type'],domain['Domain Type'],domain['Coded Values'])
    fc_json = "gdb_featureclasses.json"
    gdb_fcs = get_dict(workspace,fc_json)
    fc_field_json = "gdb_featureclass_fields.json"
    gdb_fields = get_dict(workspace,fc_field_json)
    tbl_field_json = "gdb_comments_fields.json"
    tbl_fields = get_dict(workspace,tbl_field_json)
    
    #Create Feature Classes and Geodatabase Tables
    for fc_key in gdb_fcs['FeatureClasses']:
        #fc_key = "ElectricUtilityProblemTypes"
        fc_name = gdb_fcs['FeatureClasses'][fc_key]
        fc_comment = create_gdb_featureclass(gdb,fc_name)
        for field_schema in gdb_fields['Fields']:
            add_gdb_field(gdb_path,gdb_name,fc_key,fc_name,field_schema, gdb_domains['Domains'])
        for field_schema in tbl_fields['Fields']:
            add_gdb_field(gdb_path,gdb_name,fc_key,fc_comment,field_schema, gdb_domains['Domains'])
        create_relationship_class(gdb_name,fc_name,fc_comment)
        
        
