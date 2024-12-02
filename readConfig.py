import os
import sys
import yaml


def get_file_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys.executable
    else:
        base_path = __file__

    base_dir = os.path.dirname(base_path)
    return os.path.join(base_dir, relative_path)
path = get_file_path("config.yaml")
with open(path, "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)

discordWebhook = cfg["webhook"]
if discordWebhook == "":
    discordWebhook = None
openFiles = cfg["openFiles"]
