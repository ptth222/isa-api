# Validating ISA-Tab and ISA-JSON

+++


Syntax validation is available from the ISA API. Validation comes in two flavors, whether you need validate ISA-Tab documents or want to check ISA-JSON files against the JSONSchema expression of the ISA model.

***

## Validating ISA-Tab

* To validate ISA-Tab files in a given directory `./tabdir/` against the default reference ISA xml configuration (isaconfig-default_v2015-07-02),  do the following, with for instance a folder called `BII-S-3`:

```python
from isatools import isatab
my_json_report = isatab.validate(open(os.path.join('./BII-S-3/', 'i_investigation.txt'))
```

```{admonition}  Tip
:class: tip
The validator will then read the
location of your study and assay table files from the investigation file
in order to validate those.
```

```{admonition}  Tip
:class: tip
 If no path to XML configurations is provided, the ISA API will automatically select and use the
`isaconfig-default_v2015-07-02` configurations.
```

* To validate ISA-Tab files in a given directory `./tabdir/` against a different, custoom made ISA xml configuration found in a directory
`./my_custom_covid_study_isaconfig_v2021/`, do something like the following, making sure to *point to the investigation file* of your ISA-Tab, and
providing the XML configurations. :

```python
from isatools import isatab
my_json_report = isatab.validate(open(os.path.join('./tabdir/', 'i_investigation.txt')),
								 './my_custom_covid_study_isaconfig_v2021/')
```


The validator will return a JSON-formatted report of warnings and errors, an examplar of which can be seen below:

```JSON
{"errors": [],
 "warnings": [{"message": "A required property is missing",
   "supplemental": "A property value in Investigation Title of investigation file at column 1 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Investigation Description of investigation file at column 1 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Publication DOI of investigation file at column 1 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 1 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 2 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 3 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 4 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 5 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 6 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 7 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 8 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 9 is required",
   "code": 4003},
  {"message": "A required property is missing",
   "supplemental": "A property value in Study Person Mid Initials of investigation file at column 10 is required",
   "code": 4003},
  {"message": "A value does not correspond to the correct data type",
   "supplemental": "Invalid value 'V6 and V5 for type 'list' of the field 'Parameter Value[target_subfragment]'",
   "code": 4011}],
 "info": [{"message": "Found 2 study groups in s_BII-S-7.txt",
   "supplemental": "Found 2 study groups in s_BII-S-7.txt",
   "code": 5001},
  {"message": "Found -1 study groups in a_matteo-assay-Gx.txt",
   "supplemental": "Found -1 study groups in a_matteo-assay-Gx.txt",
   "code": 5001}],
 "validation_finished": true}

```


This ISA-Tab validator has been tested against the sample data sets:
- [BII-I-1](https://github.com/ISA-tools/ISAdatasets/tree/master/tab/BII-I-1)
- [BII-S-3](https://github.com/ISA-tools/ISAdatasets/tree/master/tab/BII-S-3)
- [BII-S-7](https://github.com/ISA-tools/ISAdatasets/tree/master/tab/BII-S-7)

All of which that are found in the `isatools` package.


```{warning} 
the ISA sample datasets used to test the ISA tools also contains studies which harbour errors.
BII-S-4 and BII-S-5 will fail validation owing to an error in the investigation file (`Publication list` instead of `Publication `*L*`ist`)
```

***

### Validating ISA JSON

To validate an ISA JSON file against the ISA JSON version 1.0
specification you can use do so by doing this by doing something like:

```python
from isatools import isajson
my_json_report = isajson.validate(open('isa.json'))
```

The rules we check for in the new validators are documented in [this
working document](https://goo.gl/l0YzZt) in Google spreadsheets. Please
be aware as this is a working document, some of these rules may be
amended as we get more feedback and evolve the ISA API code.

This ISA JSON validator has been tested against [a range of dummy test
data](https://github.com/ISA-tools/ISAdatasets/tree/tests/json) found in
`ISAdatasets` GitHub repository.

The validator will return a JSON-formatted report of warnings and
errors.

***

### Batch validation of ISA-Tab and ISA-JSON

To validate a batch of ISA-Tabs or ISA-JSONs, you can use the
`batch_validate()` function.

To validate a batch of ISA-Tabs, you can do something like:

```python
from isatools import isatab
my_tabs = [
    '/path/to/study1/',
    '/path/to/study2/'
]
my_json_report = isatab.batch_validate(my_tabs, '/path/to/report.txt')
```

To validate a batch of ISA-JSONs, you can do something like

```python
from isatools import isajson
my_jsons = [
    '/path/to/study1.json',
    '/path/to/study2.json'
]
my_json_report = isajson.batch_validate(my_jsons, '/path/to/report.txt')
```

In both cases, the batch validation will return a JSON-formatted report
of warnings and errors.

***

### Reformatting JSON reports

The JSON reports produced by the validators can be reformatted using a
function found in the `isatools.utils` module.

For example, to write out the report as a CSV textfile to `report.txt`,
you can do something like:

```python
from isatools import utils
with open('report.txt', 'w') as report_file:
     report_file.write(utils.format_report_csv(my_json_report))
```
