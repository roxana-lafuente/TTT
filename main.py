"""@brief     Main module of TTT."""

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

# os is one of the modules that I know comes with 2.7, no questions asked.
import os

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from gi.repository import Gdk
    gi.require_version('WebKit', '3.0')
    from gi.repository import WebKit
except ImportError:
    print "Dependency unfulfilled, please install gi library"
    exit(1)


def install_and_import(package):
    """@brief     Imports modules and installs them if they are not."""
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        try:
            import pip
        except ImportError:
            print "no pip"
            os.system('python get_pip.py')
        finally:
            import pip
        pip.main(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)


# these other ones I a am not so sure of. Thus the install function.
install_and_import("subprocess")
install_and_import("json")
install_and_import("sys")
install_and_import("time")
install_and_import("shutil")
install_and_import("urlparse")
install_and_import("itertools")
install_and_import("webbrowser")

from commands import *
from files_processing import *
from evaluation import *
from post_editing import PostEditing
from constants import moses_dir_fn, is_valid_dir, is_valid_file, languages

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='VisualsMenu'>
      <menu action='Visuals'>
        <menuitem action='metro'/>
        <menuitem action='paper'/>
        <separator />
        <menuitem action='lights_on_option'/>
      </menu>
    </menu>
  </menubar>
</ui>
"""


class MyWindow(Gtk.Window):
    """@brief     Main window class."""

    def __init__(self):
        """@brief     Initializes the main window of TTT."""
        # Recognize OS
        if os.name == 'posix':  # Linux
            self.is_linux, self.is_windows = True, False
        elif os.name == 'nt':  # Windows
            self.is_linux, self.is_windows = False, True
        else:
            print "Unknown OS"
            exit(1)
        # Check Moses Config file.
        self.moses_dir = ""
        self.output_directory = ""
        # Main title
        Gtk.Window.__init__(self, title="Translators' Training Tool")
        self.connect('destroy', self.final_responsabilities)
        self.set_border_width(3)

        # Toolbar initialization
        action_group = Gtk.ActionGroup("my_actions")
        self.add_choices_menu_actions(action_group)
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)
        menubar = uimanager.get_widget("/MenuBar")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(menubar, False, False, 0)
        self.gtk_theme = "paper"
        self.lightsOption = "gtk"

        # Set notebook for tabs
        self.notebook = Gtk.Notebook()
        box.pack_start(self.notebook, True, True, 0)
        self.add(box)

        # Add tabs to the notebook
        self.is_corpus_preparation_ready = False
        # Corpus Preparation tab
        self._set_corpus_preparation()
        # LM & MT Training tab
        self._set_training()
        # Translation tab
        self._set_translation()
        # Evaluation tab
        self._set_evaluation()
        # Post Editing tab
        self.init_persistent_post_editing_state()
        self._set_post_editing()
        # Init
        self.source_lang = None
        self.target_lang = None
        self.original_directory = os.getcwd()

        self.notebook.set_current_page(2)

    def _check_moses_installation(self, directory):
        """@brief     Determines if directory contains moses."""
        # TODO: TRY catch OSError when permission denied!!
        file_content = [f for f in os.listdir(directory)]
        moses_files = [
            "/scripts/tokenizer/tokenizer.perl",
            "/scripts/recaser/truecase.perl",
            "/scripts/training/clean-corpus-n.perl",
            "/bin/lmplz",
            "/bin/build_binary",
            "/scripts/training/train-model.perl",
            "/bin/moses"
        ]
        if self.is_windows:
            moses_files = [f.replace("/", "\\")
                           for f in moses_files]
            moses_files = [f + ".exe"
                           for f in moses_files
                           if "/bin" in f]
        is_valid = True
        for mfile in moses_files:
            is_valid = is_valid and os.path.isfile(directory + mfile)
        return is_valid

    def is_moses_dir_valid(self, directory):
        """@brief     Determines if it contains a valid moses installation."""
        is_valid = True
        if directory == "":
            is_valid = False   # Empty string
        elif not os.path.exists(directory):
            is_valid = False  # Directory does not exist
        else:
            # Check if dir exists but does not contain moses installation
            is_valid = self._check_moses_installation(directory)

        return is_valid

    def get_moses_dir(self):
        """@brief     Gets Moses directory."""
        directory = self.moses_dir
        response = Gtk.ResponseType.ACCEPT
        while response == Gtk.ResponseType.ACCEPT and not self.is_moses_dir_valid(directory):
            label = Gtk.Label("Enter MOSES installation directory")
            entry = Gtk.Entry()
            button = Gtk.Button("Choose File")
            button.connect("clicked", self._on_dir_clicked, entry)
            dialog = Gtk.Dialog("Moses configuration",
                                None,
                                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
            box = dialog.get_content_area()
            box.add(label)
            box.add(entry)
            box.add(button)
            label.show()
            entry.show()
            button.show()
            response = dialog.run()
            directory = entry.get_text()
            dialog.destroy()

        # If it is not valid, keep asking until valid or user leaves.
        if response != Gtk.ResponseType.ACCEPT:
            exit(1)
        self.moses_dir = directory

        return directory

    def _on_languages_combo_changed(self, combo, attribute):
        """@brief     Gets the SL and TL from combo box."""
        if attribute == "ST":
            self.source_lang = combo.get_active_text()
        elif attribute == "TT":
            self.target_lang = combo.get_active_text()

    def _set_corpus_preparation(self):
        """@brief     GUI elements to run truecaser, tokenizer and cleaner."""
        self.preparation = Gtk.VBox()
        grid = Gtk.Grid()
        inside_grid = Gtk.Grid()

        # Languages Frame.
        lang_frame = Gtk.Frame(label="Languages")
        # Source language picker
        stlang_label = Gtk.Label("Source text")
        inside_grid.add(stlang_label)
        self.stlang_box = Gtk.ComboBoxText()
        self.stlang_box.set_entry_text_column(0)
        self.stlang_box.connect("changed",
                                self._on_languages_combo_changed,
                                "ST")
        for language in languages:
            self.stlang_box.append_text(language)
        inside_grid.add(self.stlang_box)

        # Target language picker
        ttlang_label = Gtk.Label("Target text")
        inside_grid.attach_next_to(ttlang_label,
                                   stlang_label,
                                   Gtk.PositionType.BOTTOM,
                                   1,
                                   1)
        self.ttlang_box = Gtk.ComboBoxText()
        self.ttlang_box.set_entry_text_column(0)
        self.ttlang_box.connect("changed",
                                self._on_languages_combo_changed,
                                "TT")
        for language in languages:
            self.ttlang_box.append_text(language)
        inside_grid.attach_next_to(self.ttlang_box,
                                   self.stlang_box,
                                   Gtk.PositionType.BOTTOM,
                                   1,
                                   1)
        inside_grid.set_column_spacing(10)
        filler = Gtk.Label("   ")
        grid.attach(filler, 0, 0, 1, 1)
        lang_frame.add(inside_grid)
        grid.add(lang_frame)

        # Output frame.
        preprocess_results_frame = Gtk.Frame(label="Results")
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_min_content_height(200)
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        preprocessResultsText = Gtk.TextView()
        preprocessResultsText.set_editable(False)
        preprocessResultsText.set_cursor_visible(False)
        preprocessResultsText.set_wrap_mode(True)
        self.preprocessResultsTextBuffer = preprocessResultsText.get_buffer()
        scrolledwindow.add(preprocessResultsText)
        preprocess_results_frame.add(scrolledwindow)
        grid.attach_next_to(preprocess_results_frame,
                            lang_frame,
                            Gtk.PositionType.BOTTOM,
                            4,  # number of columns the child will span
                            7)  # number of rows the child will span

        # Translation Model Frame.
        inside_grid = Gtk.Grid()
        tm_frame = Gtk.Frame(label="Translation Model")
        # Translation Model: Source Text Picker
        st_label = Gtk.Label("Source text")
        inside_grid.add(st_label)
        self.st_train = Gtk.Entry()
        self.st_train.set_text("")
        inside_grid.add(self.st_train)
        self.st_button = Gtk.Button("Choose File")
        self.st_button.connect("clicked", self._on_file_clicked, self.st_train)
        inside_grid.add(self.st_button)

        # Translation Model: Target Text Picker
        tt_label = Gtk.Label("Target text")
        inside_grid.attach_next_to(tt_label,
                                   st_label,
                                   Gtk.PositionType.BOTTOM,
                                   1,
                                   10)
        self.tt_train = Gtk.Entry()
        self.tt_train.set_text("")

        inside_grid.attach_next_to(self.tt_train,
                                   self.st_train,
                                   Gtk.PositionType.BOTTOM,
                                   1,
                                   1)
        self.tt_button = Gtk.Button("Choose File")
        self.tt_button.connect("clicked", self._on_file_clicked, self.tt_train)
        inside_grid.attach_next_to(self.tt_button,
                                   self.st_button,
                                   Gtk.PositionType.BOTTOM,
                                   1,
                                   1)
        inside_grid.set_column_spacing(10)
        tm_frame.add(inside_grid)
        grid.add(tm_frame)

        # Language Model Frame.
        lm_frame = Gtk.Frame(label="Language Model")
        inside_grid = Gtk.Grid()
        inside_grid.add(Gtk.Label("Source text"))
        self.lm_text = Gtk.Entry()
        self.lm_text.set_text("")
        inside_grid.add(self.lm_text)
        self.lm_button = Gtk.Button("Choose File")
        self.lm_button.connect("clicked", self._on_file_clicked, self.lm_text)
        inside_grid.add(self.lm_button)
        lm_frame.add(inside_grid)
        grid.attach_next_to(lm_frame, tm_frame, Gtk.PositionType.BOTTOM, 1, 1)

        # Output directory.
        s_frame = Gtk.Frame(label="Settings")
        inside_grid = Gtk.Grid()
        inside_grid.add(Gtk.Label("Output directory"))
        self.language_model_directory_entry = Gtk.Entry()
        self.language_model_directory_entry.set_text("")
        inside_grid.add(self.language_model_directory_entry)
        self.s_button = Gtk.Button("Choose Directory")
        self.s_button.connect("clicked",
                              self._on_dir_clicked,
                              self.language_model_directory_entry,
                              "change output directory")
        inside_grid.add(self.s_button)
        inside_grid.set_row_spacing(10)
        inside_grid.set_column_spacing(10)
        s_frame.add(inside_grid)
        grid.attach_next_to(s_frame, lm_frame, Gtk.PositionType.BOTTOM, 1, 1)

        # Start corpus preprocessing button.
        sbutton = Gtk.Button(label="Start corpus preprocessing")
        sbutton.connect("clicked", self._prepare_corpus)
        # self.preparation.set_border_width(10)
        grid.attach_next_to(sbutton, s_frame, Gtk.PositionType.BOTTOM, 1, 1)
        grid.set_row_spacing(20)
        grid.set_column_spacing(20)

        # self.preparation.add(grid)
        self.preparation.pack_start(grid,
                                    expand=True,
                                    fill=True,
                                    padding=30)
        self.notebook.insert_page(self.preparation,
                                  Gtk.Label('Corpus preparation'), 0)

    def _has_chosen_lang(self):
        """@brief     Determines if source and target language have been chosen."""
        return not self.source_lang is None and not self.target_lang is None

    def _has_chosen_preprocess_params(self, language_model_directory):
        """@brief     Determines if all data for preprocessing is ready"""
        is_ready = is_valid_dir(language_model_directory) and self._has_chosen_lang()
        is_ready = is_ready and is_valid_file(self.tt_train.get_text())
        is_ready = is_ready and is_valid_file(self.st_train.get_text())
        is_ready = is_ready and is_valid_file(self.lm_text.get_text())
        return is_ready

    def _prepare_corpus(self, button):
        """@brief     Runs moses truecaser, tokenizer and cleaner."""
        output = ""
        if self._has_chosen_preprocess_params(self.output_directory):
            language_model_directory = adapt_path_for_cygwin(self.is_windows,
                                                     self.output_directory)
            # Change directory to the language_model_directory.
            try:
                os.chdir(self.output_directory)
            except:
                # Output directory does not exist.
                os.mkdir(self.output_directory)
                os.chdir(self.output_directory)
            cmds = []
            # 1) Tokenization
            # a) Target text
            self.target_tok = generate_input_tok_fn(self.target_lang,
                                                    language_model_directory)
            cmds.append(get_tokenize_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                             self.target_lang,
                                             adapt_path_for_cygwin(self.is_windows, self.tt_train.get_text()),
                                             self.target_tok))
            # b) Source text
            self.source_tok = generate_input_tok_fn(self.source_lang,
                                                    language_model_directory)
            cmds.append(get_tokenize_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                             self.source_lang,
                                             adapt_path_for_cygwin(self.is_windows, self.st_train.get_text()),
                                             self.source_tok))
            # c) Language model
            self.lm_tok = generate_lm_tok_fn(language_model_directory)
            cmds.append(get_tokenize_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                             self.source_lang,
                                             adapt_path_for_cygwin(self.is_windows,self.lm_text.get_text()),
                                             self.lm_tok))

            # 2) Truecaser training
            # a) Target text
            cmds.append(get_truecaser_train_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                                    self.output_directory,
                                                    self.target_lang,
                                                    self.target_tok))
            # b) Source text
            cmds.append(get_truecaser_train_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                                    self.output_directory,
                                                    self.source_lang,
                                                    self.source_tok))
            # c) Language model
            cmds.append(get_truecaser_train_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                                    self.output_directory,
                                                    self.target_lang,
                                                    self.lm_tok))

            # 3) Truecaser
            self.input_true = language_model_directory + "/input.true"
            # a) Target text
            self.target_true = generate_input_true_fn(self.target_lang,
                                                      language_model_directory)
            cmds.append(get_truecaser_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                              self.output_directory,
                                              self.target_lang,
                                              self.target_tok,
                                              self.target_true))
            # b) Source text
            self.source_true = generate_input_true_fn(self.source_lang,
                                                      language_model_directory)
            cmds.append(get_truecaser_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                              self.output_directory,
                                              self.source_lang,
                                              self.source_tok,
                                              self.source_true))
            # c) Language model
            self.lm_true = generate_lm_true_fn(language_model_directory)
            cmds.append(get_truecaser_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                              self.output_directory,
                                              self.target_lang,
                                              self.target_tok, self.lm_true))

            # 4) Cleaner
            # a) Target text
            self.input_clean = generate_input_clean_fn(language_model_directory)
            self.source_clean = self.input_true + "." + self.source_lang
            self.target_clean = self.input_true + "." + self.target_lang
            cmds.append(get_cleaner_command(adapt_path_for_cygwin(self.is_windows, self.moses_dir),
                                            self.source_lang,
                                            self.target_lang,
                                            self.input_true,
                                            self.input_clean))

            # Start threads
            all_ok = True
            for cmd in cmds:
                output += "Running command: %s" % cmd
                proc = subprocess.Popen([cmd],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
                all_ok = all_ok and (proc.wait() == 0)
                out, err = proc.communicate()
                output += "Output: %s\n%s\n\n\n" % (out, err)
            if all_ok:
                self.is_corpus_preparation_ready = True
                with open(self.output_directory + '/lm.ini', 'w') as f:
                    f.write("source_lang:"+self.source_lang+"\n")
                    f.write("target_lang:"+self.target_lang+"\n")
        else:
            output += "ERROR. You need to complete all fields."
        self.preprocessResultsTextBuffer.set_text(output)
        os.chdir(self.original_directory)

    def _on_file_clicked(self, widget, labelToUpdate, tab_name = "undefined"):
        """@brief     Get file path from dialog."""
        dialog = Gtk.FileChooserDialog("Please choose a file", None,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self._add_file_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            labelToUpdate.set_text(dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            labelToUpdate.set_text("")

        if tab_name == "Machine translation":
            self.mt_out_text = os.path.dirname(dialog.get_filename())
        dialog.destroy()

    def _on_dir_clicked(self, widget, labelToUpdate, command = ""):
        """@brief     Get folder path from dialog."""
        dialog = Gtk.FileChooserDialog("Please choose a directory", None,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self._add_dir_filters(dialog)
        dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            labelToUpdate.set_text(dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            labelToUpdate.set_text("")

        if "change output directory" in command:
            self.output_directory = dialog.get_filename()
            self.post_editing_output.set_text(self.output_directory)
            self.evaluation_output.set_text(self.output_directory)
            self.mt_output.set_text(self.output_directory)

        dialog.destroy()


    def _add_dir_filters(self, dialog):
        """@brief     Add folder filters for folder choosing."""
        # TODO: Allow to only choose folders
        filter_text = Gtk.FileFilter()

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def _add_file_filters(self, dialog):
        """@brief     Add file filters for file choosing."""
        filter_text = Gtk.FileFilter()

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def _set_training(self):
        """@brief     Prepares GUI to run MT and LM training."""
        self.training = Gtk.Box()
        grid = Gtk.Grid()

        # Start training button.
        self.start_training_button = Gtk.Button("Start training")
        self.start_training_button.connect("clicked", self._train)
        grid.add(self.start_training_button)
        # Output frame.
        training_results_frame = Gtk.Frame(label="Results")
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        resultsText = Gtk.TextView()
        resultsText.set_editable(False)
        resultsText.set_cursor_visible(False)
        resultsText.set_wrap_mode(True)
        self.trainingResultsTextBuffer = resultsText.get_buffer()
        scrolledwindow.add(resultsText)
        training_results_frame.add(scrolledwindow)
        grid.attach_next_to(training_results_frame,
                            self.start_training_button,
                            Gtk.PositionType.BOTTOM,
                            1,
                            1)

        self.training.add(grid)
        self.notebook.insert_page(self.training, Gtk.Label('Training'), 1)

    def _train(self, button):
        """@brief     Runs MT and LM training."""
        language_model_directory = adapt_path_for_cygwin(self.is_windows,
                                                 self.language_model_directory_entry.get_text())
        if is_valid_dir(language_model_directory) and self.is_corpus_preparation_ready:
            os.chdir(self.language_model_directory_entry.get_text())
            cmds = []
            output = "Log:\n\n"
            # Train the language model.
            self.lm_arpa = generate_lm_fn(language_model_directory)
            cmds.append(get_lmtrain_command(self.moses_dir,
                                            self.target_lang,
                                            self.lm_true,
                                            self.lm_arpa))

            # Binarize arpa
            self.blm = generate_blm_fn(language_model_directory)
            cmds.append(get_blmtrain_command(self.moses_dir,
                                             self.target_lang,
                                             self.lm_arpa,
                                             self.blm))

            self.trainingResultsTextBuffer.set_text(output)

            # Train the translation model.
            out_file = generate_tm_fn(language_model_directory)
            cmds.append(get_tmtrain_command(self.moses_dir,
                                            self.source_lang,
                                            self.target_lang,
                                            self.blm,
                                            self.input_clean,
                                            language_model_directory))

            # TODO!
            # Binarize phase-table.gz
            # Binarize reordering-table.wbe-msd-bidirectional-fe.gz
            # Change PhraseDictionaryMemory to PhraseDictionaryCompact
            # Set the path of the PhraseDictionary feature to point to:
            # $HOME/working/binarised-model/phrase-table.minphr
            # Set the path of the LexicalReordering feature to point to:
            # $HOME/working/binarised-model/reordering-table

            for cmd in cmds:
                # use Popen for non-blocking
                output += cmd
                proc = subprocess.Popen([cmd],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
                proc.wait()
                (out, err) = proc.communicate()
                if out != "":
                    output += out
                elif err != "":
                    output += err

            # Adding output from training.out
            training = adapt_path_for_cygwin(self.is_windows, self.language_model_directory_entry.get_text()) + "/training.out"
            try:
                with open(training, "r") as f:
                    output += "\n" + f.read()
            except IOError:
                output += "Error. Unable to create moses.ini"

            # Set output to the output label.
            self.trainingResultsTextBuffer.set_text(output)
        else:
            output = "ERROR: Uncompleted preprocessing. "
            output += "Please go to the first tab and complete the process."
            self.trainingResultsTextBuffer.set_text(output)
        os.chdir(self.original_directory)

    def _set_translation(self):
        """@brief     Prepares GUI for running the decoder."""
        self.translation = Gtk.Box()
        # Machine Translation Frame.
        grid = Gtk.Grid()
        inside_grid = Gtk.Grid()
        mt_frame = Gtk.Frame(label="Machine translation")
        # Source Text Picker
        mt_in_label = Gtk.Label("Source text file")
        inside_grid.add(mt_in_label)
        self.mt_in_text = Gtk.Entry()
        self.mt_in_text.set_text("")
        inside_grid.add(self.mt_in_text)
        self.mt_in_button = Gtk.Button("Choose File")
        self.mt_in_button.connect("clicked",
                                  self._on_file_clicked,
                                  self.mt_in_text,
                                  "Machine translation")
        inside_grid.add(self.mt_in_button)

        self.mt_out_text = ""

        self.mt_out2_button = Gtk.Button("Choose a Model")
        self.mt_out2_button.connect("clicked",
                                   self._on_dir_clicked,
                                   self.language_model_directory_entry,
                                   "change output directory")
        inside_grid.attach_next_to(self.mt_out2_button,
                                   self.mt_in_button,
                                   Gtk.PositionType.RIGHT,
                                   1,
                                   50)

        self.mt_out3_button = Gtk.Button("Create a Model")
        self.mt_out3_button.connect("clicked",
                self._create_model,
                self.mt_out_text)
        inside_grid.attach_next_to(self.mt_out3_button,
                self.mt_out2_button,
                Gtk.PositionType.RIGHT,
                1,
                50)

        #  Evaluation Metrics: Output Text Picker
        ot_label = Gtk.Label("Output Directory")
        inside_grid.attach_next_to(ot_label,
                                   mt_in_label,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        self.mt_output = Gtk.Entry()
        self.mt_output.set_text("")
        inside_grid.attach_next_to(self.mt_output,
                                   self.mt_in_text,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        ot_button = Gtk.Button("Choose Directory")
        ot_button.connect("clicked",
                    self._on_dir_clicked,
                    self.mt_output,
                    "change output directory")

        inside_grid.attach_next_to(ot_button,
                        self.mt_in_button,
                        Gtk.PositionType.BOTTOM, 1, 10)

        # Start machine translation button.
        sbutton = Gtk.Button(label="Start machine translation")
        sbutton.connect("clicked", self._machine_translation)
        inside_grid.attach_next_to(sbutton,
                                   ot_button,
                                   Gtk.PositionType.BOTTOM,
                                   1,
                                   10)

        mt_frame.add(inside_grid)
        grid.add(mt_frame)

        # Output label.
        mt_training_results_frame = Gtk.Frame(label="Results")
        mtscrolledwindow = Gtk.ScrolledWindow()
        mtscrolledwindow.set_hexpand(True)
        mtscrolledwindow.set_vexpand(True)
        mtresultsText = Gtk.TextView()
        mtresultsText.set_editable(False)
        mtresultsText.set_cursor_visible(False)
        mtresultsText.set_wrap_mode(True)
        self.mttrainingResultsTextBuffer = mtresultsText.get_buffer()
        mtscrolledwindow.add(mtresultsText)
        mt_training_results_frame.add(mtscrolledwindow)
        grid.attach_next_to(mt_training_results_frame,
                            mt_frame,
                            Gtk.PositionType.BOTTOM,
                            1,
                            1)

        self.translation.add(grid)
        self.notebook.insert_page(self.translation,
                                  Gtk.Label('Machine Translation'),2)

    def _create_model(self, a, b):
        self.notebook.set_current_page(0)

    def _has_empty_last_line(self, fn):
        """@brief     Determines if last line of file is empty."""
        last_line_is_empty = False
        try:
            with open(fn, 'r') as f:
                last_line_is_empty = "\n" in (f.readlines()[-1])
        except Exception as e:
            last_line_is_empty = False
        return last_line_is_empty

    def _machine_translation(self, button):
        """@brief     Runs the decoder."""
        output = ""
        target_lang = ""
        for line in open(self.output_directory + '/lm.ini'):
            if "target_lang" in line: target_lang = line.split(':')[1]; print line
        in_file = self.mt_in_text.get_text()
        if not is_valid_file(in_file):
            output = "ERROR: %s should be a valid file." % in_file
        elif not self._has_empty_last_line(in_file):
            output = "ERROR: %s lacks an empty line at the end of the file." % in_file
        elif not target_lang:
            output = "ERROR: No Language Model could be loaded.\n(A file called lm.ini should be found at the output directory)"
        else:
            base = os.path.basename(in_file)
            out_mt_file = self.output_directory + "/" + os.path.splitext(base)[0] + "_translated." + target_lang.replace('\n','')
            in_file = adapt_path_for_cygwin(self.is_windows, in_file)
            out_mt_file = adapt_path_for_cygwin(self.is_windows, out_mt_file)
            output += "Running decoder....\n\n"
            lmdir = self.language_model_directory_entry.get_text()
            if is_valid_dir(lmdir):
                # Run the decoder.
                cmd = get_test_command(self.moses_dir,
                                       adapt_path_for_cygwin(self.is_windows, lmdir) + "/train/model/moses.ini",
                                       in_file,
                                       out_mt_file)
                # use Popen for non-blocking
                proc = subprocess.Popen([cmd],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True)
                (out, err) = proc.communicate()
                f = open(out_mt_file, 'r')
                mt_result = f.read()
                if mt_result == "":
                    if out != "":
                        output += out
                    elif err != "":
                        output += err
                else:
                    output += "Best translation: " + mt_result
                f.close()
            else:
                output += "ERROR. You need to load or create a model first."

        # Set output to the output label.
        self.mttrainingResultsTextBuffer.set_text(output)

    def _set_evaluation(self):
        self.preparation = Gtk.VBox()
        grid = Gtk.Grid()

        # Evaluation Frame.
        inside_grid = Gtk.Grid()
        texts_menu_frame = Gtk.Frame(label="Evaluation")
        # Evaluation Metrics: Source Text Picker
        st_label = Gtk.Label(" Machine translation")
        inside_grid.add(st_label)
        self.evaluation_source = Gtk.Entry()
        self.evaluation_source.set_text("")
        inside_grid.add(self.evaluation_source)
        self.st_button = Gtk.Button("Choose File")
        self.st_button.connect("clicked",
                               self._on_file_clicked,
                               self.evaluation_source)
        inside_grid.add(self.st_button)

        #  Evaluation Metrics: Reference Text Picker
        tt_label = Gtk.Label("Reference")
        inside_grid.attach_next_to(tt_label,
                                   st_label,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        self.evaluation_reference = Gtk.Entry()
        self.evaluation_reference.set_text("")
        inside_grid.attach_next_to(self.evaluation_reference,
                                   self.evaluation_source,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        self.tt_button = Gtk.Button("Choose File")
        self.tt_button.connect("clicked",
                               self._on_file_clicked,
                               self.evaluation_reference)
        inside_grid.attach_next_to(self.tt_button,
                                   self.st_button,
                                   Gtk.PositionType.BOTTOM, 1, 10)

        #  Evaluation Metrics: Output Text Picker
        ot_label = Gtk.Label("Output Directory")
        inside_grid.attach_next_to(ot_label,
                                   tt_label,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        self.evaluation_output = Gtk.Entry()
        self.evaluation_output.set_text("")
        inside_grid.attach_next_to(self.evaluation_output,
                                   self.evaluation_reference,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        ot_button = Gtk.Button("Choose Directory")
        ot_button.connect("clicked",
                               self._on_dir_clicked,
                               self.evaluation_output,
                               "change output directory")
        inside_grid.attach_next_to(ot_button,
                                   self.tt_button,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        inside_grid.set_column_spacing(10)

        texts_menu_frame.add(inside_grid)
        grid.add(texts_menu_frame)
        grid.set_row_spacing(1)
        grid.set_column_spacing(20)

        # Evaluation Metrics Frame.
        inside_grid = Gtk.Grid()
        buttons_frame = Gtk.Frame(label="Evaluation Metrics")
        # Evaluation Metrics: Evaluations Picker
        self.check_WER = Gtk.CheckButton.new_with_label("WER")
        self.check_PER = Gtk.CheckButton.new_with_label("PER")
        self.check_HTER = Gtk.CheckButton.new_with_label("HTER")
        self.check_GTM = Gtk.CheckButton.new_with_label("GTM")
        self.check_BLEU = Gtk.CheckButton.new_with_label("BLEU")
        self.check_BLEU2GRAM = Gtk.CheckButton.new_with_label("BLEU2GRAM")
        self.check_BLEU3GRAM = Gtk.CheckButton.new_with_label("BLEU3GRAM")
        self.check_BLEU4GRAM = Gtk.CheckButton.new_with_label("BLEU4GRAM")
        inside_grid.add(self.check_WER)
        inside_grid.add(self.check_PER)
        inside_grid.add(self.check_HTER)
        inside_grid.add(self.check_GTM)
        inside_grid.attach_next_to(self.check_BLEU,
                                   self.check_WER,
                                   Gtk.PositionType.BOTTOM, 1, 1)
        inside_grid.attach_next_to(self.check_BLEU2GRAM,
                                   self.check_PER,
                                   Gtk.PositionType.BOTTOM, 1, 1)
        inside_grid.attach_next_to(self.check_BLEU3GRAM,
                                   self.check_HTER,
                                   Gtk.PositionType.BOTTOM, 1, 1)
        inside_grid.attach_next_to(self.check_BLEU4GRAM,
                                   self.check_GTM,
                                   Gtk.PositionType.BOTTOM, 1, 1)
        self.evaluate_button = Gtk.Button("Start evaluation ")
        self.evaluate_button.connect("clicked", self._evaluate)
        inside_grid.attach(self.evaluate_button, 0, 2, 3, 1)
        buttons_frame.add(inside_grid)
        grid.add(buttons_frame)

        # Evaluation: Results
        inside_grid = Gtk.Grid()
        evaluation_results_frame = Gtk.Frame(label="Results")
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        resultsText = Gtk.TextView()
        resultsText.set_editable(False)
        resultsText.set_cursor_visible(False)
        resultsText.set_wrap_mode(True)
        self.resultsTextBuffer = resultsText.get_buffer()
        scrolledwindow.add(resultsText)
        evaluation_results_frame.add(scrolledwindow)
        grid.attach(evaluation_results_frame, 0, 1, 3, 1)

        self.preparation.pack_start(grid, expand=True, fill=True, padding=0)
        self.notebook.insert_page(self.preparation,
                                  Gtk.Label('Evaluation'), 3)

    def _evaluate(self, button):
        fields_filled = (self.evaluation_source.get_text()
                and self.evaluation_reference.get_text()
                and self.evaluation_output.get_text())
        files_exists = (is_valid_file(self.evaluation_source.get_text())
                and is_valid_file(self.evaluation_reference.get_text())
                and is_valid_dir(self.evaluation_output.get_text()))
        equal_ammount_of_lines = False
        if fields_filled and files_exists:
            num_lines_source = sum(1 for line in open(self.evaluation_source.get_text()))
            num_lines_reference = sum(1 for line in open(self.evaluation_reference.get_text()))
            equal_ammount_of_lines = num_lines_source == num_lines_reference
        if fields_filled and files_exists and equal_ammount_of_lines:
            # checkbox_indexes["WER","PER","HTER", "GTM", "BLEU","BLEU2GRAM","BLEU3GRAM"]
            checkbox_indexes = [False] * 8
            if self.check_WER.get_active():
                checkbox_indexes[0] = True
            if self.check_PER.get_active():
                checkbox_indexes[1] = True
            if self.check_HTER.get_active():
                checkbox_indexes[2] = True
            if self.check_GTM.get_active():
                checkbox_indexes[3] = True
            if self.check_BLEU.get_active():
                checkbox_indexes[4] = True
            if self.check_BLEU2GRAM.get_active():
                checkbox_indexes[5] = True
            if self.check_BLEU3GRAM.get_active():
                checkbox_indexes[6] = True
            if self.check_BLEU4GRAM.get_active():
                checkbox_indexes[7] = True
            result = evaluate(checkbox_indexes,
                              self.evaluation_source.get_text(),
                              self.evaluation_reference.get_text())
            evaluation_output_filename = self.evaluation_output.get_text()+"/evaluation_output.txt"
            f = open(evaluation_output_filename, 'w')
            f.write(result)
            f.close()
            self.resultsTextBuffer.set_text(result)
        if not equal_ammount_of_lines:
            self.resultsTextBuffer.set_text("ERROR. The files need to have the same ammount of lines.")
        if not fields_filled:
            self.resultsTextBuffer.set_text("ERROR. You need to complete all fields.")
        if not files_exists:
            if not is_valid_file(self.evaluation_source.get_text()):
                self.resultsTextBuffer.set_text("ERROR. The evaluation source file does not exist.")
            if not is_valid_file(self.evaluation_reference.get_text()):
                self.resultsTextBuffer.set_text("ERROR. The evaluation reference file does not exist.")
            if not is_valid_dir(self.evaluation_output.get_text()):
                self.resultsTextBuffer.set_text("ERROR. The evaluation output directory is not choosen.")

    def init_persistent_post_editing_state(self):
        self.post_editing_source_text = ""
        self.post_editing_reference_text = ""
        self.post_editing_warning_text = ""
        self.choosed_bilingual_post_editing_mode = False

    def _set_post_editing(self):
        self.notebook.remove_page(4)
        self.preparation = Gtk.VBox()
        self.postEdition_grid = Gtk.Grid()
        self.postEdition_grid.set_row_spacing(1)
        self.postEdition_grid.set_column_spacing(20)

        #  Post Editing Frame.
        PE_files_settings_frame = Gtk.Frame(label="")
        self.postEditing_file_menu_grid = Gtk.Grid()
        # Post Editing : Source Text Picker
        self.post_editing_reference_label = Gtk.Label("Select MT file")
        self.postEditing_file_menu_grid.add(self.post_editing_reference_label)
        self.post_editing_reference = Gtk.Entry()
        self.post_editing_reference.set_text(self.post_editing_reference_text)
        self.postEditing_file_menu_grid.add(self.post_editing_reference)
        self.post_editing_reference_button = Gtk.Button("Choose File")
        self.post_editing_reference_button.connect("clicked",
                                              self._on_file_clicked,
                                              self.post_editing_reference)
        self.postEditing_file_menu_grid.add(self.post_editing_reference_button)

        self.btn_check_bilingual = Gtk.CheckButton.new_with_label("bilingual")
        self.postEditing_file_menu_grid.attach_next_to(self.btn_check_bilingual, self.post_editing_reference_button, Gtk.PositionType.RIGHT, 1, 10)
        self.btn_check_bilingual.set_active(self.choosed_bilingual_post_editing_mode)
        self.btn_check_bilingual.connect("clicked", self.toggle_bilingual)


        self.post_editing_source_label = Gtk.Label("Select source file")
        self.postEditing_file_menu_grid.attach_next_to(self.post_editing_source_label, self.post_editing_reference_label, Gtk.PositionType.BOTTOM, 1, 10)
        self.post_editing_source = Gtk.Entry()
        self.post_editing_source.set_text(self.post_editing_source_text)
        self.postEditing_file_menu_grid.attach_next_to(self.post_editing_source, self.post_editing_reference, Gtk.PositionType.BOTTOM, 1, 10)
        self.post_editing_source_button = Gtk.Button("Choose File")
        self.post_editing_source_button.connect("clicked", self._on_file_clicked, self.post_editing_source)
        self.postEditing_file_menu_grid.attach_next_to(self.post_editing_source_button, self.post_editing_reference_button, Gtk.PositionType.BOTTOM, 1, 10)

        #  Post Editing: Output Text Picker
        ot_label = Gtk.Label("Output Directory")
        self.postEditing_file_menu_grid.attach_next_to(ot_label,
                                   self.post_editing_source_label,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        self.post_editing_output = Gtk.Entry()
        self.post_editing_output.set_text(self.output_directory)
        self.postEditing_file_menu_grid.attach_next_to(self.post_editing_output,
                                   self.post_editing_source,
                                   Gtk.PositionType.BOTTOM, 1, 10)
        ot_button = Gtk.Button("Choose Directory")
        ot_button.connect("clicked",
                               self._on_dir_clicked,
                               self.post_editing_output,
                               "change output directory")
        self.postEditing_file_menu_grid.attach_next_to(ot_button,
                                   self.post_editing_source_button,
                                   Gtk.PositionType.BOTTOM, 1, 10)

        # Start corpus preprocessing button.
        startPostEdition_btn = Gtk.Button(label="Start Post-editing")
        startPostEdition_btn.connect("clicked", self._check_and_run_post_edition)
        # self.preparation.set_border_width(10)
        self.postEditing_file_menu_grid.attach_next_to(startPostEdition_btn,ot_label, Gtk.PositionType.BOTTOM, 3, 1)
        self.post_editing_warning_label = Gtk.Label(self.post_editing_warning_text)
        self.postEditing_file_menu_grid.attach_next_to(self.post_editing_warning_label,startPostEdition_btn, Gtk.PositionType.RIGHT, 1, 1)

        PE_files_settings_frame.add(self.postEditing_file_menu_grid)
        self.postEdition_grid.add(PE_files_settings_frame)

        #self.postEdition_grid.add(self.postEditing_file_menu_grid)
        self.preparation.pack_start(self.postEdition_grid, expand=True, fill=True, padding =0)
        self.notebook.insert_page(self.preparation, Gtk.Label('Post Editing'), 4)
        self.post_editing_source_label.set_no_show_all(True)
        self.post_editing_source.set_no_show_all(True)
        self.post_editing_source_button.set_no_show_all(True)
        self.post_editing_source_label.set_no_show_all(True)

        visibility = self.btn_check_bilingual.get_active()
        self.choosed_bilingual_post_editing_mode = visibility
        self.post_editing_source_label.set_visible(visibility)
        self.post_editing_source.set_visible(visibility)
        self.post_editing_source_button.set_visible(visibility)
        self.post_editing_source_label.set_visible(visibility)

        self.notebook.show_all()

    def toggle_bilingual(self,button):
        visibility = self.btn_check_bilingual.get_active()
        self.choosed_bilingual_post_editing_mode = visibility
        self.post_editing_source_label.set_visible(visibility)
        self.post_editing_source.set_visible(visibility)
        self.post_editing_source.set_text("")
        self.post_editing_source_button.set_visible(visibility)
        self.post_editing_source_label.set_visible(visibility)
    def _check_and_run_post_edition(self, object):
        self.post_editing_source_text = self.post_editing_source.get_text()
        self.post_editing_reference_text = self.post_editing_reference.get_text()

        fields_filled = (
                (self.post_editing_source.get_text() or not self.btn_check_bilingual.get_active())
                and self.post_editing_reference.get_text()
                and self.post_editing_output.get_text())
        files_exists = (
                (is_valid_file(self.post_editing_source.get_text())  or not self.btn_check_bilingual.get_active())
                and is_valid_file(self.post_editing_reference.get_text())
                and is_valid_dir(self.post_editing_output.get_text()))

        self.post_editing_warning_text = ""
        equal_ammount_of_lines = True
        if fields_filled and files_exists:
            self.post_editing_warning_label.set_text("")
            if (self.post_editing_source.get_text() or not self.btn_check_bilingual.get_active()):
                if self.post_editing_source.get_text():
                    num_lines_source = sum(1 for line in open(self.post_editing_source_text))
                    num_lines_reference = sum(1 for line in open(self.post_editing_reference_text))
                    equal_ammount_of_lines = num_lines_source == num_lines_reference
                    self.post_editing_warning_label.set_text("The files need to have the same ammount of lines.")
                if equal_ammount_of_lines:
                    post_editing_source_text = self.post_editing_source.get_text()
                    post_editing_reference_text = self.post_editing_reference.get_text()
                    self._set_post_editing()
                    self.notebook.set_current_page(4)
                    # binding of the buttons events to the PostEditing methods
                    self.PostEditing = PostEditing(
                        post_editing_source_text,  # so that it can read the source file
                        post_editing_reference_text,  # so that it can read the reference file
                        self.notebook,  # so that it can add the diff tab when needed
                        self.postEdition_grid, # so that it can add search entry and table
                        self.output_directory,# so that it can save files on the output directory
                        self.btn_check_bilingual.get_active()) # so that it knows wether to render a monolingual or bilingual table

        if not fields_filled:
            self.post_editing_warning_label.set_text("ERROR. You need to complete all fields.")
        elif not files_exists:
            if not is_valid_file(self.evaluation_source.get_text()):
                self.post_editing_warning_label.set_text("ERROR. The source file does not exist.")
            if not is_valid_file(self.evaluation_reference.get_text()):
                self.post_editing_warning_label.set_text("ERROR. The reference file does not exist.")
            if not is_valid_dir(self.evaluation_output.get_text()):
                self.post_editing_warning_label.set_text("ERROR. The output directory is not choosen.")


    def gtk_change_visuals(self, light_option="unchanged", theme="unchanged"):
        if Gtk.MAJOR_VERSION >= 3 and Gtk.MINOR_VERSION >= 14:
            css_filename = "gtk"
            filename = ""
            if theme == "metro" or theme == "paper":
                self.gtk_theme = theme
            if light_option == "gtk" or light_option == "gtk-dark":
                self.lightsOption = light_option
            filename = 'gui/' + self.gtk_theme + '/'+ self.lightsOption + '.css'
            css = open(filename, 'r')

            style_provider = Gtk.CssProvider()
            css_data = css.read()
            css.close()

            style_provider.load_from_data(css_data)

            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                style_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def add_choices_menu_actions(self, action_group):
        self.preferences_button = Gtk.Action("VisualsMenu", "Preferences", None, None)
        action_group.add_action(self.preferences_button)
        action_visualsmenu = Gtk.Action("Visuals", "Visuals", None, None)
        action_group.add_action_with_accel(action_visualsmenu, None)
        action_group.add_radio_actions([
            ("metro", None, "metro", None, None, 1),
            ("paper", None, "paper", None, None, 2)
        ], 2, self.on_menu_choices_changed)

        lights_on_widget = Gtk.ToggleAction("lights_on_option",
                                            "Turn lights off",
                                            None, None)
        lights_on_widget.connect("toggled", self.on_menu_choices_toggled)
        action_group.add_action(lights_on_widget)

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()
        uimanager.add_ui_from_string(UI_INFO)
        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def on_menu_choices_changed(self, widget, current):
        self.gtk_change_visuals(light_option="unchanged",
                                theme=current.get_name())

    def on_menu_choices_toggled(self, widget):
        if widget.get_active():
            self.gtk_change_visuals(light_option="gtk-dark", theme="unchanged")
        else:
            self.gtk_change_visuals(light_option="gtk", theme="unchanged")

    def final_responsabilities(self, widget=None):
        if hasattr(self, 'PostEditing'):
            self.PostEditing.saveChangedFromPostEditing()
            self.PostEditing.delete_generated_files()

win = MyWindow()
win.set_name('TTT')
win.gtk_change_visuals(light_option="gtk", theme="paper")
win.connect("delete-event", Gtk.main_quit)

style_provider = Gtk.CssProvider()

style_provider.load_from_path("css/style.css")

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

win.show_all()
Gtk.main()


# TODOs
# 1- Check that files source and target have at least 100 lines.
# 2- Add buttons for choosing number of cores to use and other parameters.
