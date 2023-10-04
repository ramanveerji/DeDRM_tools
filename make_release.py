#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A wrapper script to generate zip files for GitHub releases.

This script tends to be compatible with both Python 2 and Python 3.
'''

from __future__ import print_function

import os
import shutil


DEDRM_SRC_DIR = 'DeDRM_plugin'
DEDRM_SRC_TMP_DIR = 'DeDRM_plugin_temp'
DEDRM_README= 'DeDRM_plugin_ReadMe.txt'
OBOK_SRC_DIR = 'Obok_plugin'
OBOK_README = 'obok_plugin_ReadMe.txt'
RELEASE_DIR = 'release'

def patch_file(filepath):
    with open(filepath, "rb") as f:
        fn = open(f"{filepath}.tmp", "wb")
        with open(os.path.join(DEDRM_SRC_DIR, "__calibre_compat_code.py"), "rb") as patch:
            patchdata = patch.read()
        while True:
            line = f.readline()
            if len(line) == 0:
                break

            if line.strip().startswith(b"#@@CALIBRE_COMPAT_CODE@@"):
                fn.write(patchdata)
            else:
                fn.write(line)

    fn.close()
    shutil.move(f"{filepath}.tmp", filepath)



def make_release(version):
    try:
        shutil.rmtree(RELEASE_DIR)
    except:
        pass
    try:
        shutil.rmtree(DEDRM_SRC_TMP_DIR)
    except:
        pass

    os.mkdir(RELEASE_DIR)

    # Copy folder 
    shutil.copytree(DEDRM_SRC_DIR, DEDRM_SRC_TMP_DIR)

    # Modify folder
    try: 
        shutil.rmtree(os.path.join(os.path.abspath(DEDRM_SRC_TMP_DIR), "__pycache__"))
    except:
        pass

    # Patch file to add compat code.
    for root, dirs, files in os.walk(DEDRM_SRC_TMP_DIR):
        for name in files:
            if name.endswith(".py"):
                patch_file(os.path.join(root, name))


    # Package
    shutil.make_archive(DEDRM_SRC_DIR, 'zip', DEDRM_SRC_TMP_DIR)
    shutil.make_archive(OBOK_SRC_DIR, 'zip', OBOK_SRC_DIR)
    shutil.move(f'{DEDRM_SRC_DIR}.zip', RELEASE_DIR)
    shutil.move(f'{OBOK_SRC_DIR}.zip', RELEASE_DIR)
    shutil.copy(DEDRM_README, RELEASE_DIR)
    shutil.copy(OBOK_README, RELEASE_DIR)
    shutil.copy("ReadMe_Overview.txt", RELEASE_DIR)

    # Remove temp folder:
    shutil.rmtree(DEDRM_SRC_TMP_DIR)

    release_name = 'DeDRM_tools' if version is None else f'DeDRM_tools_{version}'
    result = shutil.make_archive(release_name, 'zip', RELEASE_DIR)
    try:
        shutil.rmtree(RELEASE_DIR)
    except:
        pass
    return result


if __name__ == '__main__':
    import sys
    try:
        version = sys.argv[1]
    except IndexError:
        version = None

    print(make_release(version))
