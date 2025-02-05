# bench-llm

A Crucible benchmark wrapper for [llm-load-test](https://github.com/openshift-psap/llm-load-test).
To launch a test, run this on the Crucible controller: `crucible run --from-file run-llm.json`

All options from the llm-load-test config file are present in run-llm.json prefixed by `config_`.

## Getting Started

### Prerequisites

1. Access to your SUT. If your are targeting a RHEL SUT, you need SSH access. If you are targeting an
OpenShift SUT, you need the kubeconfig file, or SSH access to a host that has the kubeconfig file.
2. Access to a Crucible controller that has `bench-llm` installed.
3. A model endpoint accessible to your SUT. For most cases this model is running on your SUT.

### Launching The Benchmark

The suggested way to initiate a Crucible benchmark is by passing a JSON configuration file to the `run` command like this:
```
$ crucible run --from-file <path/to/config.json>
```
This configuration file will contain everything that Crucible needs to run your benchmark. If you are planning to target a RHEL SUT,
then you can use [run-llm.json](run-llm.json) as a starting point. Similarly, if you are targeting OpenShift, you can use [run-llm-openshift.json](run-llm-openshift.json).
These _will not_ run out of the box.

Firstly, under `.benchmarks[0].mv-params.sets[0].params`, configure the parameters of your llm-load-test run.
Each of these settings are specific to this benchmark. `repo_tag` lets you select a tagged version
of the llm-load-test repo to use in the benchmark,
otherwise, every other parameter is a one-for-one flattened version of
the parameters allowed in a llm-load-test config file.
Configure these as you would for any normal llm-load-test run, and make sure the
`config_plugin_options_host` is accessible on your SUT.
You'll notice the `vals` key maps to a list. By default there is only one value in `vals`,
however, you may list multiple values in this list and Crucible will automatically launch multiple
iterations of the benchmark and index them appropriately.
For instance, to try multiple concurrency values in one run you can set:
```
...
    {
      "arg": "config_load_options_concurrency",
      "vals": [
        "1",
        "2",
        "4"
      ]
    },
...
```

Next, we just need to tell Crucible where to run your test.

- __If you're targeting RHEL__: Simply replace `.endpoints[0].host` with the address of
your SSH accessible SUT. Crucible will SSH into this host to run the benchmark.

- __If you're targeting OpenShift__: Replace `.endpoints[0].host` with the address of a machine that has access to the cluster kubeconfig.
Note that this machine _should not_ be the SUT. If the cluster was installed using a bastion, this can be the bastion.
Otherwise, just copy your kubeconfig to the controller you are using and keep the default `localhost` host value.
This will use the controller itself. Make sure to also fill in `.endpoints[0].controller-ip` with the IP of the controller you are running the benchmark from.

With your run configured you can finally launch the test using:
```
$ crucible run --from-file=<your/config/file.json>
```

### Inspecting the Results

The results of your run are stored in the OpenSearch instance on the controller, in the [CommonDataModel](https://github.com/perftool-incubator/CommonDataModel)(CDM) format.
You can query these results manually with the OpenSearch query language, but it is often easier to use premade tools to simplify the process.
For our purposes, the most important CDM concepts to understand are `runs` and `iterations`. Whenever you use `crucible run ...` a unique `run` object will be created in OpenSearch.
Every time a `run` needs to start a new iteration, an `iteration` object will be created.
Put simply, a new iteration is required for every new combination of parameters. For example, if we provided three concurrency values, three iterations will be required.
Each of these `runs` and `iterations` are uniquely identified in OpenSearch with uuid's.

The last thing `crucible run ...` will output is an overview of the results that were created.
Make a note of the run uuid and the iteration uuid's.

```
...
run-id: 4a0e230c-6ece-4dab-8279-2686ffbb60b5
  tags: topology=none
  benchmark: llm
  common params: < all of the param values that were used > 
  metrics:
    source: sar-net
      types: L2-Gbps packets-sec
    source: mpstat
      types: Busy-CPU NonBusy-CPU
    source: procstat
      types: interrupts-sec
    source: llm
      types: < all of the possible metrics we can query >
    source: iostat
      types: avg-req-size-kB avg-service-time-ms kB-sec operations-merged-sec operations-sec percent-merged avg-queue-length percent-utilization
    source: sar-mem
      types: Page-faults-sec KB-Paged-in-sec KB-Paged-out-sec Pages-freed-sec Pages-swapped-in-sec Pages-swapped-out-sec reclaimed-pages-sec VM-Efficiency kswapd-scanned-pages-sec scanned-pages-sec
    source: sar-scheduler
      types: Load-Average-01m Load-Average-05m Load-Average-15m Process-List-Size Run-Queue-Length
    source: sar-tasks
      types: Context-switches-sec Processes-created-sec
    iteration-id: 7659F3C2-E412-11EF-85C3-A0383E9CC027
      unique params:
      primary-period name: measurement
      samples:
        sample-id: 80DFF8F0-E412-11EF-9ABD-B2E68BC21BD1
          primary period-id: 80E08E82-E412-11EF-94B1-CBE719288AEF
          period range: begin: 1738795188000 end: 1738795255000
          period length: 67 seconds
            result: (llm::throughput) samples: 30.533333 mean: 30.533333 min: 30.533333 max: 30.533333 stddev: NaN stddevpct: NaN
...
```

Then on the controller try running:
```
$ python3 query.py --runs=4a0e230c-6ece-4dab-8279-2686ffbb60b5 --metric-types=throughput,ttft-max --params=config_load_options_concurrency
                      run-uuid                  iteration-uuid  config_load_options_concurrency                     metric_type                           value
     4a0e230c-6ece-4dab-827...       7659F3C2-E412-11EF-85C...                               1                      throughput              30.533333333333335
     4a0e230c-6ece-4dab-827...       7659F3C2-E412-11EF-85C...                               1                        ttft-max               575.4344463348389
```

This will fetch the results of the test from OpenSearch and print you a table of throughput and ttft-max metrics that llm-load-test generated.
If there are multiple iterations in your run, you can select them using `--iterations`. By default every iteration is selected. You can also dump this table to a
JSON or CSV file automatically with the `-o` flag. Since there are usually more parameters to the test than you care to see in the output, all of them are hidden by default.
If you'd like to add a column for a particular parameter value, like `config_load_options_concurrency` in the example above, you may pass a list of parameters to the `--params` flag.
See the `--help` output for more options and details.

## Querying the Results

You can use the included `query.py` script to retrieve the results from the benchmark run. Many other usage metrics from tools may have been
uploaded to the OpenSearch database as well, but this script will help you download the relevant llm-load-test metrics so you may
more easily plot and analyze them.
```
usage: query.py [-h] [--runs RUNS] [--iterations ITERATIONS] [--metric-types METRIC_TYPES] [--params PARAMS] [-o OUTPUT] [--sql]

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
  --sql                 print the SQL that will run against OpenSearch
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
