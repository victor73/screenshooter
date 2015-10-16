#!/usr/bin/env python26

import ConfigParser
import sys
import os
import subprocess
import json
import argparse
import executor

def get_config(args):
    conf_file = args.conf

    # Create the configuration parser object
    config = ConfigParser.ConfigParser()

    if not os.path.isfile(conf_file):
        sys.stderr.write("Configuration file %s does not exist.\n" % args.conf)
        sys.exit(1)

    # Read the specified configuration file
    config.read(conf_file)

    return config

def scan_sitedir(site_dir):
    job_files = []

    # Scan the directory for JSON files
    for site_file in os.listdir(site_dir):
        if site_file.endswith(".json"):
            job_files.append(site_file)

    return job_files


def get_args():
    parser = argparse.ArgumentParser(description='Save a screen capture of website.')

    parser.add_argument('-s', '--site',
                        dest="site",
                        help="Path to a website's json configuration file")

    parser.add_argument('-c', '--conf',
                        dest='conf',
                        required=True,
                        help="Path to the configuration file")

    parser.add_argument('-d', '--dir',
                        dest="dir",
                        required=False,
                        help="Directory to scan for job files.")


    args = parser.parse_args()

    return args


def main():
    args = get_args()
    config = get_config(args)

    default_timeout = None
    phantomjs = None
    section = "global"

    # Get the default timeout value, to be used for sites that do not have a configured timeout
    if config.has_option(section, "default_timeout"):
        default_timeout = int(config.get(section, "default_timeout"))
    else:
        sys.stderr.write("Config file %s does not have a %s 'default_timeout' option.\n" % args.conf)
        sys.exit(1)

    # Get the path to the phantomjs binary and make sure that it
    # is actually there and installed.
    if not config.has_option(section, "phantomjs"):
        sys.stderr.write("Config file %s does not have a %s 'phantomjs' option.\n" % args.conf)
        sys.exit(1)
    else:
        phantomjs = config.get(section, "phantomjs")
        phantomjs = phantomjs.strip()

        if not (os.path.isfile(phantomjs) and os.path.os.access(phantomjs, os.X_OK)):
            sys.stderr.write("PhantomJS binary doesn't exist or isn't " +\
                             "executable at at %s\n" % phantomjs)
            sys.exit(1)

    site_dir = args.dir

    if site_dir == None:
        # Try to get the site diretory from the configuration file
        site_dir = config.get(section, "site_dir")
    else:
        if not os.path.isdir(site_dir):
            sys.stderr.write("Specified path %s is not a directory.\n" % site_dir)
            sys.exit(1)

    job_files = scan_sitedir(site_dir)

    phantomjs_opts = None
    if config.has_option(section, "phantomjs_opts"):
        config.get(section, "phantomjs_opts")

    if len(job_files) == 0:
        sys.stderr.write("No jobs found at %s\n" % site_dir)
        sys.exit(1)
    else:
        for job_file in job_files:
            job_file_path = os.path.abspath(os.path.join(site_dir, job_file))
            handle = open(job_file_path, "r")
            json_data = handle.read()
            handle.close()
            job_json = json.loads(json_data)

            site_name = os.path.basename(job_file)
            print("Generating screencapture for site %s." % site_name)

            # Get the configurable parameters for this site
            viewport = job_json['viewport']
            useragent = None
            if 'useragent' in job_json:
                user_agent = job_json['useragent']

            output = None
            if 'output' not in job_json:
                raise Exception("Site %s file %s doesn't have a configured 'output' path." % (site_name, job_file))
            else:
                output = job_json['output']

            # Get the timeout for this job (in seconds)
            if "timeout" in job_json:
                timeout = int(job_json['timeout'])
            else:
                timeout = default_timeout

            command = [ phantomjs ]
            if phantomjs_opts != None:
                command.append(phantomjs_opts)

            self = os.path.abspath(__file__)
            self_dir = os.path.dirname(self)
            phantomjs_script = os.path.abspath(os.path.join(self_dir, "..", "js", "screenshot.js"))
            print(phantomjs_script)
            command.extend([ phantomjs_script, job_file_path ])

            (exit_value, stdout, stderr) = executor.run_command(command)

            if exit_value != 0:
                sys.stderr.write("Error with site %s." % site_name)
                sys.stderr.write(stderr)

main()
