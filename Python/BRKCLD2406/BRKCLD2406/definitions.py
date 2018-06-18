import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

print(ROOT_DIR)

resource = 'modules'
curr_file = sys.argv[0]
path_name = os.path.dirname(curr_file)
base_path = (os.path.abspath(path_name))
res_path = base_path + "\\" + resource + "\\"

print(res_path)
