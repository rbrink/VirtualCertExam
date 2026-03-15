import os
import json, yaml
from datetime import timedelta

import vcesim.config.config_utils as cfg_utils

CONFIG_LOCATION = "./vcesim/config/"
vcesim_config_path = os.path.join(CONFIG_LOCATION, "vcesim.yaml")

def _load_config(filepath):
    with open(filepath, 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

# vcesim config, open and read yaml contents
# handle vcesim.yaml migration here
# 1. Load both current and template vcesim.yaml
cur_config = _load_config(vcesim_config_path)
new_config = _load_config("./setup/vcesim.yaml")

# 2. If the dicts do not have the same number of keys
if len(cur_config) != len(new_config):
    # 3. Update new dict with current values
    for key in cur_config:
        if key in new_config:
            new_config[key] = cur_config[key]
    # 4. Save the dictionary
    with open("./vcesim/ui/comments.json", 'r') as comments_file:
        comments = json.load(comments_file)
    vcesim_cfg = comments['VCESIM_CFG_GROUPS']['BEGIN'] + "\n\n"
    for key, value in dict(new_config).items():
        # Add any grouping comments
        vcesim_cfg += cfg_utils.yaml_check_groups(comments, key)
        # Check for comments for this key in comments.json, add them if they exist
        try:
            vcesim_cfg += '\n' + comments[str(key)] + '\n' if comments[str(key)] != "" else ""
        except KeyError:
            vcesim_cfg += '\n'
        # test if key value is an int
        value = str(value)
        try:
            post_value = int(value)
            vcesim_cfg += f"{key}: {post_value}\n"
        except ValueError:
            # Test if value is Boolean
            vcesim_cfg += cfg_utils.yaml_test_bool(key, value)
    with open(vcesim_config_path, 'w') as settings_file:
        settings_file.write(vcesim_cfg)
        settings_file.close()

vcesim_config = _load_config(vcesim_config_path)

class Config:
    SECRET_KEY = cfg_utils.generate_key()
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + vcesim_config['DBFILE']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=vcesim_config['REMEMBER_COOKIE_DURATION'])    # How long the remember me cookie lasts (default: 365 days)
    REMEMBER_COOKIE_NAME = 'remember_token'          # Cookie name (default: 'remember_token')
    REMEMBER_COOKIE_SECURE = True                    # Only send cookie over HTTPS (recommended for production)
    REMEMBER_COOKIE_HTTPONLY = True                  # Prevent JavaScript access to the cookie
    REMEMBER_COOKIE_SAMESITE = 'Lax'                 # Restrict cookie to same-site requests
