import re, os
import secrets
from pathlib import Path
from dotenv import load_dotenv, set_key

def generate_key():
    env_file = Path(".env")
    
    # Now this will correctly evaluate to True if the key was in the .env file!
    if not os.environ.get("SECRET_KEY"):
        key = secrets.token_hex(16)
        
        # set_key from dotenv is safer than appending; it creates the file if 
        # missing and safely adds/updates the key without writing duplicate lines.
        set_key(dotenv_path=env_file, key_to_set="SECRET_KEY", value_to_set=key)
        
        os.environ['SECRET_KEY'] = key
        
    return os.environ['SECRET_KEY']

def yaml_check_groups(comments, key):
    """
    Check the current key to be added to vcesim.yaml and insert the group
    separator comment, if the key matches\n
    :param comments: comments dict, containing all comments from the vcesim.yaml
    :param key: the current post key from form.args
    :return: vcesim.yaml config with any new comments added
    """
    comment_groups = {'INSTALLEDPATH': "\n" + comments['VCESIM_CFG_GROUPS']['DIR_SETUP'],
                      'WEBSERVER_IP': "\n" + comments['VCESIM_CFG_GROUPS']['WEB_SERVER']}
    if key in comment_groups:
        vcesim_cfg = comment_groups[key]
    else:
        vcesim_cfg = ""
    return vcesim_cfg


def yaml_test_bool(key, value):
    """
    we need to test if the key is a bool, as we need to lower() it for yaml\n\n
    or check if key is the webserver ip. \nIf not we need to wrap the value with quotes\n
    :param key: the current key
    :param value: the current value
    :return: the new updated vcesim.yaml config with new key: values
    """
    if value.lower() == 'false' or value.lower() == "true":
        vcesim_cfg = f"{key}: {value.lower()}\n"
    else:
        # If we got here, the only key that doesn't need quotes is the webserver key
        # everything else needs "" around the value
        if key == "WEBSERVER_IP":
            vcesim_cfg = f"{key}: {value.lower()}\n"
        else:
            # This isn't intended to be safe, it's to stop breakages - replace all non escaped quotes with escaped
            escaped = re.sub(r"(?<!\\)[\"\'`]", r'\"', value)
            vcesim_cfg = f"{key}: \"{escaped}\"\n"
    return vcesim_cfg
