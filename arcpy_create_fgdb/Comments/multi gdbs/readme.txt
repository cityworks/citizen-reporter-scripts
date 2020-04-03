--General Information--
-Creates multiple File Geodatabases in the correct schema of Crowdsource Reporter integration with Cityworks. 

-Each File Geodatabase can be published in AGOL or ArcGIS Enterprise as Feature Services, then configured with Web Maps.

-Crowdsource Reporter app uses Web Maps for vizualization, customize pop-ups as needed

-create_multi_fgdb_comments.py uses ArcPy, compatible with the Python/ArcPy environment included with ArcMap Python 2.7 or ArcGIS Pro Python 3.X


--Included Files--
-create_multi_fgdb_comments.py ~ Run in the same folder as the JSON files described below

-gdb_acc_domains.json ~ "Geodatabase Accessory Domains", schema for Field Domains that will apply to all geodatabses, such as Status values.

-gdb_comments_fields.json ~ "Geodatabase Comments Fields", schema for fields that will be added to the related tables for constituent comments.

-gdb_featureclass_fields.json ~ "Geodatabase Feature Class Fields", schema for fields that will be added to the feature classes in each File Geodatabase.

-gdb_featureclasses.json ~ "Geodatabase Feature Classes", "Mapping Key" for python logic. Maps which "Problem Type" Field Domain applies to which Feature Class.
For example: "AirportProblemTypes": "AirportProblems", AirportProblemTypes in the field domain that will be applied to the ProblemType field in the AirportProblems feature class.

-gdb_problemtype_domains.json ~ "Geodatabase Problem Types Domains", schema for Field Domains that are specific for the Feature Class to which they are mapped to above.

-example_config.json ~ A sample of the schema of json file used when deploying the "connect_to_cityworks.py" script from Esri. A "config.json" file is the output of the Connect2Cityworks.pyt 
Geoprocessing tool. The tool can be difficult to work with. One can use the provided sample schema in example_config.json and fill in the blanks.


--CUSTOMIZATION--
-To add more problem types, follow the same pattern in the gdb_problemtype_domains.json file, the pattern matches specifications used in the arcpy.CreateDomain_management function.

-Map the problem types domain to a new feature class in gdb_featureclasses.json

-REMEMBER: The ProblemType Domain Code MUST match the "Code" field of the Service Request Template VERBATIM


Good luck and happy integrating!
Mitchell Ottesen
Cityworks