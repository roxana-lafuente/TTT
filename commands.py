"""@brief     Contains moses' commands constructors."""

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
from constants import *


def get_background_command(background):
    """@brief     Runs a command in background."""
    return " &" if background else ""


def get_tokenize_command(mdir, language, in_file, out_file, background=False):
    """@brief     Constructs tokenizer command."""
    amp = get_background_command(background)
    return "%s -l %s < %s > %s %s\n" % (tokenizer % mdir,
                                        language,
                                        in_file,
                                        out_file,
                                        amp)


def get_truecaser_train_command(mdir, odir, lang, corpus, background=False):
    """@brief     Constructs truecaser training command."""
    amp = get_background_command(background)
    return "%s --model %s --corpus %s %s\n" % (truecaser_train % mdir,
                                               model % (odir, lang),
                                               corpus,
                                               amp)


def get_truecaser_command(mdir, odir, lang, in_file, out_file, background=False):
    """@brief     Constructs truecaser command."""
    amp = get_background_command(background)
    return "%s --model %s < %s > %s %s\n" % (truecaser % mdir,
                                             model % (odir, lang),
                                             in_file,
                                             out_file,
                                             amp)


def get_cleaner_command(mdir,
                        in_lang,
                        out_lang,
                        in_file,
                        out_file,
                        background=False):
    """@brief     Constructs cleaner command."""
    amp = get_background_command(background)
    return "%s %s %s %s %s 1 80 %s\n" % (cleaner % mdir,
                                         in_file,
                                         out_lang,
                                         in_lang,
                                         out_file,
                                         amp)


def get_lmtrain_command(mdir, language, in_file, out_file, background=False):
    """@brief     Constructs language model training command."""
    amp = get_background_command(background)
    return "%s < %s > %s %s\n" % (lm_train % mdir, in_file, out_file, amp)


def get_blmtrain_command(mdir, language, in_file, out_file, background=False):
    """@brief     Constructs binarize language model command."""
    amp = get_background_command(background)
    return "%s %s %s %s\n" % (blm_train % mdir, in_file, out_file, amp)


def get_tmtrain_command(mdir,
                        in_lang,
                        out_lang,
                        lm_file,
                        corpus,
                        output_dir,
                        background=False):
    """@brief     Constructs train machine translation command."""
    amp = get_background_command(background)
    cmd = tm_train % mdir

    cmd += " -cores 6 -corpus " + corpus + " -f " + in_lang + " -e " + out_lang
    cmd += " -alignment grow-diag-final-and -reordering msd-bidirectional-fe "
    cmd += "-lm 0:3:" + lm_file.replace("~", "$HOME") + " -external-bin-dir "
    cmd += mdir + "/scripts >& " + output_dir + "/" + train_fn
    return cmd + amp + "\n"


def get_test_command(mdir, moses_ini, in_file, out_file, background=False):
    """@brief     Constructs run decoder command."""
    amp = get_background_command(background)
    return "%s %s < %s > %s %s\n" % (test % mdir,
                                     moses_ini,
                                     in_file,
                                     out_file,
                                     amp)
