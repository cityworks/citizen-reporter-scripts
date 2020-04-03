# Cityworks Citizen Reporter Scripts

Scripts and tools to assist Cityworks customers integrate with the ArcGIS Citizen Reporter configurable application

## Getting Started

Once you have configured a Citizen Reporter app in ArcGIS Online. Use the Connect2Cityworks ArcGIS Pro tool to generate a config.json file
or fill out the provided example file. Use the config.json file as a command line argument when running the connect_to_cityworks.py script.

### Prerequisites

ArcGIS Pro 2.2+ Python 3.5+, ArcGIS API for Python 1.4.1+

### Installing

To execute the script that transfers data between ArcGIS and Cityworks, configure an application such as Windows Task Scheduler.

1. Open Windows Task Scheduler
2. Click Action > Create Task and provide a name for the task.
3. Click the Action tab and click New.
4. Set Action to Start a Program.
5. Browse to the location of your Python 3 installation (for example, <default directory>\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-python3\python.exe).
6. In the Add arguments text box, copy the name of the script (connect_to_cityworks.py) and the path to the configuration file save from running the tool in ArcGIS Pro.The script name and the configuration file path must be separated by a script, and the configuration file path must be surrounded with double quotes if it contains any spaces.
7. In the Start in text box, type the path to the folder containing the scripts and email templates and click OK.
8. Click the Trigger tab, click New, and set a schedule for your task.
9. Click OK.


## License

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

## Acknowledgments

* Allison Muise, Esri
