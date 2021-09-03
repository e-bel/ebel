# e(BE:L) Tests
These tests run fine so long as the user has a valid admin account setup for the test DB. The enrich tests automatically import
[this test file](data/import_tests/basic_import_test.bel.json) and must be able to add/delete entries as needed.

The API tests require that the user has [the base import file](data/import_tests/basic_import_test.bel.json) already
imported using the following commands:
```bash
$ ebel import-json ./data/import_tests/basic_import_test.bel.json -e -u userName -p myODBpassword -d ebel_test -h localhost -p 2424
```