# OPTAIN tools
A collection of scripts and other snippets developped during the [OPTAIN Project](https://www.optain.eu).
## General information
The following codes are QGIS processing scripts. To install them, download the desired file, 
go to the Processing Toolbox, from the script icon, select "Add script to toolbox". 
Finally select the algorithm from the list under Scripts &rarr; Optain tools 
### merge_small_features.py
A processing script that merges small features based on the area. 
Small features are merged with the adjacent shape with the longest common edge.
The user can give more weight to the adjacent shape of the same group.
#### List of parameters
- Input layer = the vector layer with small polygons (please use single feature type)
- Area limits = the smallest area limit in map units
- Name field = the field with the id/name of the polygon (useful to recognize the wrong element in case of error)
- Group field = the field in the attribute table that defines similar polygons that will be merged according to the weight factor
- PHI field = a numeric attribute that define the degree of perviousness of the merged shape
- Weight factor = a number that define the weight to assign to the length between common edges 
  (if zero, edges length is zero between polygon of the same group)

<img src="./img/merge_small_features_schema.svg">

#### Notes
- merge_small_feature_DATA.zip contains test_case.gpkg with small features. 
Set Area limits to 5000, the Name field to "name", the Group field to "group" 
and the PHI field to "phi" and Weight factor to 2. The result should be similar 
test_case_simply.gpkg.
- use "Delete holes" for QGIS processing to remove empty spaces inside the resulting polygons

### clean_overlap.py
A processing script that adjusts edges in order to remove overlaps between polygons. 

### join_nodes_links.py
Add the link id to the closest point  

### find_common_edges.py
Return the common edges between adjacent polygons
