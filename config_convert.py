import json
from typing import Any, List, Tuple, Union, Dict
import yaml
import sys

def flatten(d: Union[Dict[str, Any], List[Any]], prefix="") -> List[Tuple[str, Any]]:
    elems = []
    if type(d) is list:
        print("We cannot flatten a list")
        sys.exit(1)
    if type(d) is dict:
        for k, v in d.items():
            if type(v) is dict:
                elems.extend(flatten(v, prefix=(prefix+"_"+k)))
            elif type(v) is list:
                elems.extend(flatten(v, prefix=(prefix+"_"+k)))
            else:
                elems.append(((prefix+"_"+k), str(v)))
    return elems

def template(d: Union[Dict[str, Any], List[Any]], prefix="") -> Dict:
    resd = {}
    if type(d) is list:
        print("We cannot flatten a list")
        sys.exit(1)
    if type(d) is dict:
        for k, v in d.items():
            if type(v) is dict:
                resd[k] = template(dict(v), prefix=(prefix+"_"+k))
            elif type(v) is list:
                print("We cannot flatten a list")
                sys.exit(1)
            else:
                resd[k] = "{{ " + prefix + "_" + k + " }}"
    return resd

def main():
    if len(sys.argv) != 2:
        print(f"Incorrect number of arguments: {len(sys.argv)}")
        sys.exit(1)

    file_name = sys.argv[1]

    y = {}
    with open(file_name, "r") as f:
        y = yaml.safe_load(f)
    flat = flatten(y, prefix="config")
    params = {"params": [{"arg": param[0], "vals": [param[1]]} for param in flat]}
    print("========================================================")
    print("================= Crucible JSON Params =================")
    print("========================================================")
    print(json.dumps(params, indent=4))
    print("========================================================")
    print("================= Crucible Script Vars =================")
    print("========================================================")
    print("dict(")
    print("\t" + "\n\t".join([f"{param[0]} = {repr(param[1])}," for param in flat]))
    print(")")
    print("========================================================")
    print("============ llm-load-test Config Template =============")
    print("========================================================")
    print(yaml.dump(template(y, prefix="config")))

if __name__ == "__main__":
    main()
