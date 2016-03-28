#!/usr/bin/env python
"""
Parse pole and zero txt file
"""
from __future__ import print_function
import os
from obspy import UTCDateTime
import re
import numpy as np
from pprint import pprint


def split_content(content):
    """
    split multiple instruments in one pz file. Split them by
    the '* *********************' line in between.
    """
    star_count = 0
    split_pzs = []
    for idx, line in enumerate(content):
        # searching for starting line
        match = re.match(r"\* (\*)+", line)
        if match:
            break

    content = content[(idx + 1):]

    pz_info = []
    for line in content:
        match = re.match(r"\* (\*)+", line)
        if match:
            star_count += 1
            if star_count % 2 == 0:
                split_pzs.append(pz_info)
                pz_info = []
        else:
            pz_info.append(line)
    split_pzs.append(pz_info)

    if (star_count + 1) % 2 != 0:
        raise ValueError("Number of star lines(%d) is odd, meaning the pz "
                         "file is not complete")

    return split_pzs


def __extract_float_values(content, array):

    for idx, line in enumerate(content):
        number_pattern = r"\s*([-+]?\d*\.\d+|\d+)"
        match = re.match(number_pattern, line)
        if match:
            values = line.split()
            array[idx, 0] = float(values[0])
            array[idx, 1] = float(values[1])
        else:
            break


def _get_zeros(content):
    """
    Extract zeros information from content
    """
    for idx, line in enumerate(content):
        match = re.match(r"ZEROS (\d+)", line)
        if match:
            nzeros = int(match.group(1))
            start_idx = idx + 1
            break

    zeros = np.zeros([nzeros, 2])
    __extract_float_values(content[start_idx:(start_idx + nzeros)], zeros)

    return zeros


def _get_poles(content):
    """
    Matching poles information from content
    """
    # matching poles
    for idx, line in enumerate(content):
        match = re.match(r"POLES (\d+)", line)
        if match:
            npoles = int(match.group(1))
            start_idx = idx + 1
            break

    poles = np.zeros([npoles, 2])
    __extract_float_values(content[start_idx:(start_idx + npoles)], poles)

    return poles


def _get_header(content):
    """
    Matching header information in pz files
    """
    header_dict = {}
    for line in content:
        match = re.match(r"\*", line)
        if match:
            colon_idx = line.index(':')
            key = line[1:colon_idx].strip()
            value = line[(colon_idx+1)::].strip()
            header_dict[key] = value
    _convert_datatype(header_dict)
    return header_dict


def _convert_datatype(info):
    for key, value in info.iteritems():
        if key in ["LOCATION", ]:
            continue
        try:
            info[key] = float(value)
        except Exception:
            pass

    datetime_keys = ("START", "END", "CREATED")
    for key in datetime_keys:
        if key not in info:
            continue
        if info[key] == 'N/A':
            continue
        info[key] = UTCDateTime(info[key])


def extract_pz_info(content):
    """
    Extract the pz information from txt content for one instrument
    """
    info = {}

    info["HEADER"] = _get_header(content)
    info["ZEROS"] = _get_zeros(content)
    info["POLES"] = _get_poles(content)

    # matching CONSTANT
    for line in content:
        match = re.match(r"CONSTANT\s+(\S+)", line)
        if match:
            info["CONSTANT"] = float(line.split()[1])

    return info


def parse_pz(filename):

    if isinstance(filename, str):
        with open(filename) as fh:
            content = fh.readlines()
    elif isinstance(filename, file):
        content = fh.readlines()

    content = [line.rstrip("\n") for line in content]
    split_pzs = split_content(content)

    pz_info_list = []
    for pz in split_pzs:
        pz_info_list.append(extract_pz_info(pz))

    return pz_info_list


if __name__ == "__main__":

    testfile = os.path.join(
        "test_data",
        "SAC_PZs_II_ALE")

    #testfile = os.path.join(
    #    "test_data",
    #    "SAC_PZs_IU_YSS_BHZ_00_" +
    #    "2009.067.00.00.00.0000_99999.9999.24.60.60.99999")

    #testfile = os.path.join(
    #    "test_data",
    #    "SAC_PZs_IU_ULN_BHZ_00_" +
    #    "2012.058.21.57.00.0000_99999.9999.24.60.60.99999")

    pz = parse_pz(testfile)
    pprint("Pole zero information")
    pprint(pz)
