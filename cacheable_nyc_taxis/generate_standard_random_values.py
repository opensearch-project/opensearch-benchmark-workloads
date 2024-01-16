from .query_value_providers import fn_value_generators
import json
import os


NUM_VALUES = 5000 # number of standard queries to generate by default

# if a standard query is in here, generate this many instead (for example if there are few possible values)
num_values_exceptions = {
    "cheap_passenger_count":50,
}
for fn_name in fn_value_generators: 
    #print("Generating values for {}".format(fn_name))
    fp = os.path.dirname(os.path.realpath(__file__)) + "/" + "standard_values/{}_values.json".format(fn_name)
    val_dict = []
    for i in range(num_values_exceptions.get(fn_name, NUM_VALUES)): # default to NUM_VALUES
        val_dict.append(fn_value_generators[fn_name]())
    with open(fp, "w") as f:
        f.write(json.dumps(val_dict))
