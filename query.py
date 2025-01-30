#!/usr/bin/env python3
# -*- mode: python; indent-tabs-mode: nil; python-indent-level: 4 -*-
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import sys
import json
from typing import List
import argparse
import opensearchpy

def sql(client, query) -> List:
    return client.transport.perform_request(
        "POST",
        "/_plugins/_sql",
        body={"query": query}
    )["datarows"]

def truncstr(s, limit=10) -> str:
    if len(s) > limit:
        return s[:limit-3] + "..."
    else:
        return s

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", help="list of run uuids to fetch results for, ex: <uuid-1>,<uuid-2>,<uuid-3>...")
    parser.add_argument("--iterations", help="list of run iterations to fetch results for, ex: <uuid-1>,<uuid-2>,<uuid-3>...")
    parser.add_argument("--metric-types", help="list of metric types to fetch results for, ex: <name-1>,<name-2>,<name-3>...")
    parser.add_argument("--params", help="list of parameters from payload to include with the output")
    parser.add_argument("-o", "--output", help="path to create output file, format is determined by file extension. '.json'/'.csv' supported")
    parser.add_argument("--sql", action="store_true", help="print the SQL that will run against OpenSearch")
    args = parser.parse_args()

    runs: List[str] = args.runs.split(",") if args.runs is not None else []
    iterations: List[str] = args.iterations.split(",") if args.iterations is not None else []
    metric_types: List[str] = args.metric_types.split(",") if args.metric_types is not None else []
    params: List[str] = args.params.split(",") if args.params is not None else []

    host = 'localhost'
    port = 9200
    auth = ('admin', 'admin')

    # Create the client with SSL/TLS enabled, but hostname verification disabled.
    client = opensearchpy.OpenSearch(
        hosts = [{'host': host, 'port': port}],
        http_compress = True, # enables gzip compression for request bodies
        http_auth = auth,
        use_ssl = False,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
    )

    raw_query = "SELECT [cdm_metric_desc.run.run-uuid] as run-uuid, [cdm_metric_desc.iteration.iteration-uuid] as iteration-uuid, [cdm_metric_desc.metric_desc.type] as metric_type, [cdm_metric_data.metric_data.value] as value FROM cdmv8dev-metric_desc cdm_metric_desc JOIN cdmv8dev-metric_data cdm_metric_data ON [cdm_metric_desc.metric_desc.metric_desc-uuid]=[cdm_metric_data.metric_desc.metric_desc-uuid] WHERE [iteration] IS NOT NULL {};"


    run_filter = "(" + " OR ".join([f"[cdm_metric_desc.run.run-uuid] = '{r}'" for r in runs]) + ")"
    iteration_filter = "(" + " OR ".join([f"[cdm_metric_desc.iteration.iteration-uuid] = '{i}'" for i in iterations]) + ")"
    metric_type_filter = "(" + " OR ".join([f"[cdm_metric_desc.metric_desc.type] = '{t}'" for t in metric_types]) + ")"

    filters = []
    if len(runs) > 0: filters.append(run_filter)
    if len(iterations) > 0: filters.append(iteration_filter)
    if len(metric_types) > 0: filters.append(metric_type_filter)

    final_filter = "" if len(filters) == 0 else " AND " + " AND ".join(filters)
    final_query = raw_query.format(final_filter)
    if args.sql: print(f"Running:\n{final_query}\n\n")
    results = sql(client, final_query)

    cols = ["run-uuid", "iteration-uuid"] + [*params] + ["metric_type", "value"]

    # OpenSearch SQL doesn't allow you to join more than 2 indices :(
    if len(params) > 0:
        params_raw_query = "SELECT iteration.iteration-uuid, param.arg, param.val FROM cdmv8dev-param WHERE {}"
        relevant_iterations = list({result[1] for result in results})
        param_filter = "(" + " OR ".join([f"[param.arg] = '{p}'" for p in params]) + ")"
        iteration_filter = "(" + " OR ".join([f"[iteration.iteration-uuid] = '{i}'" for i in relevant_iterations]) + ")"

        combined_filter = []

        combined_filter.append(param_filter)
        if len(relevant_iterations) > 0: combined_filter.append(iteration_filter)

        final_param_filter = " AND ".join(combined_filter)
        params_final_query = params_raw_query.format(final_param_filter)
        if args.sql: print(f"Running:\n{params_final_query}\n\n")
        params_results = sql(client, params_final_query)
        if len(params_results) == 0:
            print("ERROR: no matching params found")
            return 1

        arg_dict = {}
        for params_result in params_results:
            if params_result[0] not in arg_dict:
                arg_dict[params_result[0]] = {}

            arg_dict[params_result[0]][params_result[1]] = params_result[2]
        for result in results:
            param_entries = [arg_dict[result[1]][param] for param in params]
            result.insert(2, *param_entries)

    row_format ="{:>30}  " * (len(cols))
    print(row_format.format(*cols))
    for row in results:
        row_format = ""
        for e in row:
            row_format += "{:>30}  ".format(truncstr(e, limit=25))
        print(row_format)

    if args.output is not None:
        with open(args.output, "w") as f:
            if ".json" in args.output:
                d = []
                for result in results:
                    o = {}
                    for n in range(len(result)):
                        o[cols[n]] = result[n]
                    d.append(o)

                json.dump(d, f)
            elif ".csv" in args.output:
                csv_str = "\n".join([",".join(cols)] + [",".join(result) for result in results])
                f.write(csv_str)
            else:
                print(f"WARNING: not sure how to write file with associated file extension {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
