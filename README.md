# bench-llm

A Crucible benchmark wrapper for [guidellm](https://github.com/neuralmagic/guidellm).
To launch a test, run this on the Crucible controller: `crucible run --from-file run-llm.json`

All options from the guidellm config file are present in run-llm.json prefixed by `guidellm`. This includes all options that are exposed exclusively as environment variables. Please see the `Params` class in [llm-client](llm-client) for a full list.

## Getting Started

### Prerequisites

1. Access to your SUT. If your are targeting a RHEL SUT, you need SSH access. If you are targeting an
OpenShift SUT, you need the kubeconfig file, or SSH access to a host that has the kubeconfig file.
2. Access to a Crucible controller that has `bench-llm` installed.
3. A model endpoint accessible to your SUT. For most cases this model is running on your SUT.
4. A HuggingFace token in a file `/root/hf_token` on the controller. This is necessary to access a model's tokenizer.

### Launching The Benchmark

The suggested way to initiate a Crucible benchmark is by passing a JSON configuration file to the `run` command like this:
```
$ crucible run --from-file <path/to/config.json>
```
This configuration file will contain everything that Crucible needs to run your benchmark. If you are planning to target a RHEL SUT,
then you can use [run-llm.json](run-llm.json) as a starting point. Similarly, if you are targeting OpenShift, you can use [run-llm-openshift.json](run-llm-openshift.json).
These _will not_ run out of the box.

Firstly, under `.benchmarks[0].mv-params.sets[0].params`, configure the parameters of your guidellm run.
Configure these as you would for any normal guidellm run. But make sure the
`guidellm_target` is accessible on your SUT.
You'll notice the `vals` key maps to a list. By default there is only one value in `vals`,
however, you may list multiple values in this list and Crucible will automatically launch multiple
iterations of the benchmark and index them appropriately.
For instance, to try multiple dataset profiles in one run you can set:
```
...
    {
      "arg": "guidellm_data",
      "vals": [
        "prompt_tokens=128,output_tokens=128,prompt_tokens_stdev=32,output_tokens_stdev=32",
        "prompt_tokens=512,output_tokens=64,prompt_tokens_stdev=32,output_tokens_stdev=32"
      ]
    },
...
```

Next, we just need to tell Crucible where to run your test.

- __If you're targeting RHEL__: Simply replace `.endpoints[0].host` with the address of
your SSH accessible SUT. Crucible will SSH into this address to run your benchmark.
You must have passwordless SSH access. Crucible will raise an error if hit with a password prompt.

- __If you're targeting OpenShift__: Replace `.endpoints[0].host` with the address of a machine that has access to the cluster kubeconfig.
Note that this machine _should not_ be the SUT. If the cluster was installed using a bastion, this can be the bastion.
Otherwise, just copy your kubeconfig to the controller you are using and keep the default `localhost` host value.
This will use the controller itself.
Even if you are just using `localhost`, you must have passwordless SSH access to this host. Crucible will raise an error if prompted for a password.
Make sure to also fill in `.endpoints[0].controller-ip` with the IP of the controller you are running the benchmark from.

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

## Querying the Results

You can use the included `query.py` script to retrieve the results from the benchmark run. Many other usage metrics from tools may have been
uploaded to the OpenSearch database as well, but this script will help you download the relevant guidellm metrics so you may
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
