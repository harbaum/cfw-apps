#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

# Improvements:
# - run manifest through configparser
#   - only transfer entries needed for the store app
#   - make sure no mandatory entry is missing
# - check if zip file needs to be rebuild
#   - rebuild zip file automatically

import sys
import os

print("Building package index ...")

pkgfile = open("00packages", "w")
pkgfile.write("; list of packages\n")
pkgfile.write("; this file contains all manifests\n")

# scan the directory for app directories
for l in sorted(os.listdir(".")):
    if os.path.isdir(l):
        m = os.path.join(l, "manifest")
        if os.path.isfile(m):
            print("Adding", l, "...")
            pkgfile.write("\n")
            pkgfile.write("["+l+"]\n")
            lang = ""

            # copy manifest contents. Skip [app] entry
            f = open(m)
            for line in f:
                line = line.strip()
                # ignore empty lines
                if line != "":
                    # check if there's a section header in the line
                    if line[0] == '[':
                        # check if it's no the app section
                        if not "[app]" in line:
                            lang = line[line.find("[")+1:line.find("]")]
                    else:
                        if lang == "":
                            # print lines not from a language specific section
                            # just as they are
                            print(line, file=pkgfile)
                        else:
                            # otherwise append language code to identifier
                            # split at first ':'
                            parts = line.split(':', 1)
                            print(parts[0].strip()+"_"+lang+": "+parts[1].strip(), file=pkgfile)
            f.close()

pkgfile.close()
