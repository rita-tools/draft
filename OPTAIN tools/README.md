# OPTAIN tools
A collection of scripts and other snippets developped during the [OPTAIN Project](https://www.optain.eu).
## General information
The following codes are QGIS processing scripts. To install them, download the desired file, 
go to the Processing Toolbox, from the script icon, select "Add script to toolbox". 
Finally select the algorithm from the list under Scripts &rarr; Optain tools 
### merge_small_features.py
A processing script that merges small features based on the area. 
Small features are merge with the adiacent shape with the longest common edge. The user can gives more weigth to the adiacent shape of the same group.
#### List of parameters
- Input layer = the vector layer with small polygons (please use single feature type)
- Area limits = the smallest area limit in map units
- Name field = the field with the id/name of the polygon (useful to recognize the wrong element in case of error)
- Group field = the field in the attribute table that defines similar polygons that will be merged according to the weight factor
- PHI field = a numeric attribute that define the degree of perviousness of the merged shape
- Weight factor = a number that define the weigth to assign to the length between common edges (is zero, edges length is zero between polygon of the same group)

Note: merge_small_feature_DATA.zip contains test_case.gpkg with small features. Set Area limits to 5000, the Name field to "name", the Group field to "group" and the PHI field to "phi" and Weight factor to 2. The result should be similar test_case_simply.gpkg.
