# bench-llm

A Crucible benchmark wrapper for [llm-load-test](https://github.com/openshift-psap/llm-load-test).
To launch a test, run this on the Crucible controller: `crucible run --from-file run-llm.json`

All options from the llm-load-test config file are present in run-llm.json prefixed by `config_`.

## Retrieve The Results

You can use the included `query.py` script to retrieve the results from the benchmark run. Many other usage metrics from tools may have been
uploaded to the OpenSearch database as well, but this script will help you download the relevant llm-load-test metrics so you may
more easily plot and analyze them.
```
usage: query.py [-h] [--runs RUNS] [--iterations ITERATIONS] [--metric-types METRIC_TYPES] [--params PARAMS] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  --runs RUNS           list of run uuids to fetch results for, ex: <uuid-1>,<uuid-2>,<uuid-3>...
  --iterations ITERATIONS
                        list of run iterations to fetch results for, ex: <uuid-1>,<uuid-2>,<uuid-3>...
  --metric-types METRIC_TYPES
                        list of metric types to fetch results for, ex: <name-1>,<name-2>,<name-3>...
  --params PARAMS       list of parameters from payload to include with the output
  -o OUTPUT, --output OUTPUT
                        path to create output file, format is determined by file extension. '.json'/'.csv' supported
```

## Files Included

- [config.yaml.j2](config.yaml.j2): Template file to generate [llm-load-test](https://github.com/openshift-psap/llm-load-test) config
- [config_convert.py](config_convert.py): This script is not used in the benchmark. It is a helper for us to generate `config.yaml.j2` and some other
boilerplate from a full llm-load-test config file.
- [llm-base](llm-base): Boilerplate for Crucible. This was copied from `bench-ilab` directly.
- [llm-client](llm-client): Core script that downloads llm-load-test, templates the config file, and runs llm-load-test.
- [llm-get-runtime](llm-get-runtime): Required by Crucible. Simple script that calculates how much time our benchmark will run for. Requests an indefinite runtime.
- [llm-load-test-config.yaml](llm-load-test-config.yaml): This file is also not directly used in the benchmark. It is used in conjunction with `config_convert.py` to generate
a template file and other boilerplate.
- [llm-post-process](llm-post-process): Core script that processes any artifact and generates a CommonDataModel payload. At this point, the only data being considered is the output json file from llm-load-test.
- [multiplex.json](multiplex.json): Required by Crucible. Allows you to use regex to perform input validation.
- [random-but-same](random-but-same): Random bytes to be used as some randomness if needed (not currently used).
- [rickshaw.json](rickshaw.json): Required by Crucible. Tells Crucible where to find your scripts (`llm-client`, `llm-post-process`, etc) and any other files you want to copy into the run.
- [run-llm.json](run-llm.json): Used to run and configure your benchmark. It is not a necessary file to make the benchmark work, but a copy with all parameters listed is given here for your convenience. This file is used when running the benchmark `crucible run --from-file run-llm.json`
- [workshop.json](workshop.json): Required by Crucible. Specifies necessary dependencies to include in the container that will run on the SUT. It is used to install the dependencies required by llm-load-test.
