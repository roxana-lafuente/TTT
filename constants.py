"""@brief     Contains constants common to all modules of TTT."""
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
try:
    import os
except:
    print "Dependency unfulfilled, please install os library"
    exit(1)

# Language codes.
ENG = "en"
FR = "fr"
DE = "de"


def adapt_path_for_cygwin(is_windows, directory):
    """@brief     Adapts a linux path to a windows one."""
    assert len(directory) > 0
    adapted_directory = "/cygdrive/"
    if is_windows:
        if directory[1:3] == ":\\":
            adapted_directory += directory[0] + "/" + directory[3:].replace("\\", "/")
        else:
            adapted_directory = directory.replace("\\", "/")
    else:
        adapted_directory = directory
    return adapted_directory

def is_valid_dir(directory):
    """
    @brief     Determines if a directory is valid.

    @returnReturns True if directory is valid, False otherwise.
    """
    is_valid = directory is not None and directory != ""
    is_valid = is_valid and os.path.exists(directory)
    is_valid = is_valid and os.path.isdir(directory)
    return is_valid

def is_valid_file(filepath):
    """
    @brief     Determines if a file is valid.

    @returnReturns True if directory is valid, False otherwise.
    """
    is_valid = filepath is not None and filepath != ""
    is_valid = is_valid and os.path.exists(filepath)
    is_valid = is_valid and os.path.isfile(filepath)
    return is_valid

# Languages we show in the GUI to work with Moses.
languages = [ENG, FR, DE]

# Config file where info from Moses is saved.
moses_dir_fn = "moses.config"

# Filenames.
train_fn = "training.out"

# Check OS
is_win = os.name == 'nt'

# Moses commands
tokenizer = adapt_path_for_cygwin(is_win, "%s/scripts/tokenizer/tokenizer.perl ")

truecaser_train = adapt_path_for_cygwin(is_win, "%s/scripts/recaser/train-truecaser.perl ")
model = adapt_path_for_cygwin(is_win, "%s/truecase-model.%s")

truecaser = adapt_path_for_cygwin(is_win, "%s/scripts/recaser/truecase.perl ")

cleaner = adapt_path_for_cygwin(is_win, "%s/scripts/training/clean-corpus-n.perl ")

lm_train = adapt_path_for_cygwin(is_win, "%s/bin/lmplz ") + "-o 3 "  # TODO: Should be chosen by the user.

blm_train = adapt_path_for_cygwin(is_win, "%s/bin/build_binary ")

tm_train = "nohup nice " + adapt_path_for_cygwin(is_win, "%s/scripts/training/train-model.perl") + " -root-dir train "

test = adapt_path_for_cygwin(is_win, "%s/bin/moses") + " -f "
