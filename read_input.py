import json
import os


def read_test(test_name):
    json_file = open(os.path.join("./tests", test_name + ".json"), 'r')
    loaded_test_json = json_file.read()
    rules = json.loads(loaded_test_json)
    json_file.close()

    return rules


