# Import Tests
This folder contains various BEL files, and their generated e(BE:L) ready JSONs, used for testing the import feature
of e(BE:L). These are imported to the test database.  

## Files
##### basic_import_test.bel
Used for checking if the basic import functionality works and that the update_from_protein2gene feature works properly.
Only contain one relation consisting of 2 protein nodes. Should result in:
* 2 protein nodes
* 2 RNA nodes
* 2 gene nodes
* 1 increases edge
* 2 translated_to edges
* 2 transcribed_to edges 