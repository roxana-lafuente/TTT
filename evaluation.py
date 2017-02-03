# !/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# PyKeylogger: TTT for Linux and Windows
# Copyright (C) 2016 Roxana Lafuente <roxana.lafuente@gmail.com>
#                    Miguel Lemos <miguelemosreverte@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import subprocess
import os
import platform

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def filterTER (lines):
    result = ''
    warning = False
    lines = lines.splitlines()
    for line in lines:
        if "Total TER:" in line:
            result += line.replace("Total TER:","")
        if "Warning, Invalid line:" in line:
            warning = True
    if warning:
        result += " There are lines unchanged from source to reference. HTER cannot work in those cases."
    return result + "\n"

def filterBLEU (line, BLEU_type):
    if BLEU_type == "BLEU":      line = line.split(',', 1)[0]
    if BLEU_type == "BLEU2GRAM": line = line.split(',', 1)[1].split('/')[0]
    if BLEU_type == "BLEU3GRAM": line = line.split(',', 1)[1].split('/')[1]
    if BLEU_type == "BLEU4GRAM": line = line.split(',', 1)[1].split('/')[2]
    line = line.replace('\n','').replace('\r', '')
    return line

def filterGTM (line):
    if "You should not be comparing equal runs" in line:
        line = "There are lines unchanged from source to reference. GTM cannot work in those cases.\n"
    return line

def filter_output(proccess,method):
    out, err = proccess.communicate()
    final_text = ""
    if not err :
        final_text = out
    else: final_text = err
    if method == "TER": final_text = filterTER(final_text)
    if method == "GTM": final_text = filterGTM(final_text)

    return final_text

cached_results = {}

def evaluate(checkbox_indexes, test, reference):
    checkbox_indexes_constants = ["WER","PER","HTER", "GTM", "BLEU","BLEU2GRAM","BLEU3GRAM","BLEU4GRAM"]
    DIRECTORY = os.path.abspath("evaluation_scripts") + "/"
    TER_DIRECTORY = DIRECTORY + "tercom-0.7.25/tercom.7.25.jar"
    GTM_DIRECTORY = DIRECTORY + "gtm-1.3-binary/gtm.jar"
    EXEC_PERL = "perl "
    EXEC_JAVA = "java "
    return_results = ""
    checkbox_index = 0
    BLEU_cached_results = ""
    for checkbox in checkbox_indexes:
        if checkbox:
            key = (test,creation_date(test),reference,creation_date(reference), checkbox_indexes_constants[checkbox_index])
            if key in cached_results: return_results += cached_results[key]
            else:
                if checkbox_indexes_constants[checkbox_index] == "WER" or checkbox_indexes_constants[checkbox_index] == "PER":
                    command = EXEC_PERL + DIRECTORY +  checkbox_indexes_constants[checkbox_index] + ".pl" + " -t " + test + " -r " + reference
                    proc = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE)
                    result = "\n" + checkbox_indexes_constants[checkbox_index] + "..... " + proc.stdout.read()
                    return_results += result
                    cached_results[key] =  result

                if checkbox_indexes_constants[checkbox_index] == "HTER":
                    command_2 = EXEC_JAVA + "-jar " + TER_DIRECTORY + " -r " + reference + " -h " + test
                    proc = subprocess.Popen(command_2, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    result = "\n" + checkbox_indexes_constants[checkbox_index] + "....." + filter_output(proc,"TER")
                    return_results += result
                    cached_results[key] =  result


                if checkbox_indexes_constants[checkbox_index] == "GTM":
                    command_2 = EXEC_JAVA + "-jar " + GTM_DIRECTORY + " -t " +  test + " " + reference
                    proc = subprocess.Popen(command_2, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    result = "\n" + checkbox_indexes_constants[checkbox_index] + "....." + filter_output(proc,"GTM")

                    #out, err = proc.communicate()
                    #result = "\n" + checkbox_indexes_constants[checkbox_index] + "....." + out + err
                    return_results += result
                    cached_results[key] =  result

                if "BLEU" in checkbox_indexes_constants[checkbox_index] and BLEU_cached_results == "":
                    command = EXEC_PERL + DIRECTORY + "BLEU.pl " + reference +" < " + test
                    proc = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    while True:
                      line = proc.stdout.readline()
                      if line != '':BLEU_cached_results += line
                      else: break

                if "BLEU" in checkbox_indexes_constants[checkbox_index]:
                    result = "\n" + checkbox_indexes_constants[checkbox_index] + "..... "\
                        + filterBLEU(BLEU_cached_results,checkbox_indexes_constants[checkbox_index])
                    return_results += result
                    cached_results[key] =  result


        checkbox_index += 1
    return_results
    return return_results
