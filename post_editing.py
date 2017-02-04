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

#os is one of the modules that I know comes with 2.7, no questions asked.
import os
import datetime

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

try:
    import webbrowser
except ImportError:
    print "Dependency unfulfilled, please install webbrowser library"
    exit(1)

try:
    import json
except ImportError:
    print "Dependency unfulfilled, please install json library"
    exit(1)

try:
    import sys
except ImportError:
    print "Dependency unfulfilled, please install sys library"
    exit(1)

try:
    import time
except ImportError:
    print "Dependency unfulfilled, please install time library"
    exit(1)

try:
    import shutil
except ImportError:
    print "Dependency unfulfilled, please install os library"
    exit(1)

try:
    import urlparse
except ImportError:
    print "Dependency unfulfilled, please install os library"
    exit(1)

try:
    import itertools
except ImportError:
    print "Dependency unfulfilled, please install os library"
    exit(1)

from table import Table
import html_injector

class PostEditing:

    def __init__(self, post_editing_source, post_editing_reference, notebook, grid, output_directory, bilingual = False):
        self.post_editing_source = post_editing_source
        self.post_editing_reference = post_editing_reference
        self.translation_tab_grid = grid
        self.notebook = notebook
        self.modified_references =  []
        self.saved_modified_references = []
        filename = os.path.splitext(os.path.basename(post_editing_reference))[0]
        self.output_directory = output_directory + "/"  + filename + "_" + str(datetime.date.today().strftime("%B_%d_%Y"))
        if not os.path.exists(self.output_directory): os.makedirs(self.output_directory)
        self.bilingual = bilingual

        self.tables = {}
        self.log = {}
        self.HTML_view = WebKit.WebView()
        uri = "statistics/generated/stats.html"
        uri = os.path.realpath(uri)
        uri = urlparse.ParseResult('file', '', uri, '', '', '')
        uri = urlparse.urlunparse(uri)
        self.HTML_view.load_uri(uri)
        filename = post_editing_reference[post_editing_reference.rfind('/'):]
        filename_without_extension = os.path.splitext(filename)[0]
        filename_extension = os.path.splitext(filename)[1]
        self.saved_origin_filepath = self.output_directory + filename


        self.tables["translation_table"] =  Table("translation_table",self.post_editing_source,self.post_editing_reference, self.preparePostEditingAnalysis_event,self.preparePostEditingAnalysis, self.calculate_statistics_event, self.translation_tab_grid, self.output_directory, self.bilingual)

        self.source_log_filepath = self.output_directory + '/log.json'


        shutil.rmtree("./statistics/generated", ignore_errors=True)
        os.makedirs(os.path.abspath("statistics/generated"))

        self.translation_tab_grid.show_all()
        self.tables["translation_table"].save_post_editing_changes_button.hide()
        self.tables["translation_table"].insertions_statistics_button.hide()
        self.tables["translation_table"].deletions_statistics_button.hide()
        self.tables["translation_table"].time_statistics_button.hide()

    def calculate_time_per_segment(self):
        if self.log.keys():
            seconds_spent_by_segment = {}
            percentaje_spent_by_segment = {}
            total_time_spent = 0
            #again with the closure, lets see how it plays out.
            def pairwise(iterable):
                a, b = itertools.tee(iterable)
                next(b, None)
                return itertools.izip(a, b)

            now = int(time.time()*1000)
            myList = sorted(self.log.keys())
            my_source_log = self.log
            my_source_log[now] = self.log[myList[-1]]

            #calculate time spent by segment
            for current_timestamp,next_timestamp in pairwise(sorted(my_source_log.keys())):
                #for current_timestamp,next_timestamp in sorted(self.log.keys()):
                delta = (int(next_timestamp) - int(current_timestamp))/1000
                for segment_index in my_source_log[current_timestamp]:
                    if segment_index in seconds_spent_by_segment:
                        seconds_spent_by_segment[segment_index] += delta
                    else:
                        seconds_spent_by_segment[segment_index] = delta
            #calculate total time spent
            for a in seconds_spent_by_segment:
                total_time_spent += seconds_spent_by_segment[a]
            #calculate percentajes
            for a in seconds_spent_by_segment:
                percentaje_spent_by_segment[a] = float(seconds_spent_by_segment[a]) *100 / float(max(1,total_time_spent))


            title = "<th>Segment </th><th>" + '%'+ " of the time spent </th>"
            return self.build_pie_as_json_string(percentaje_spent_by_segment),self.build_table(percentaje_spent_by_segment),title
        else:
            return [],[],""

    def calculate_deletions_per_segment(self):
        percentaje_spent_by_segment=self.tables["translation_table"].calculate_insertions_or_deletions_percentajes(True)
        title = "<th>Segment </th><th>" + '%'+ " of deletions made</th>"
        return self.build_pie_as_json_string(percentaje_spent_by_segment),self.build_table(percentaje_spent_by_segment),title
    def calculate_insertions_per_segment(self):
        percentaje_spent_by_segment=self.tables["translation_table"].calculate_insertions_or_deletions_percentajes(False)
        title = "<th>Segment </th><th>" + '%'+ " of insertions made</th>"
        return self.build_pie_as_json_string(percentaje_spent_by_segment),self.build_table(percentaje_spent_by_segment),title
    def format_table_data(self, segment_index, table_contents, monolingual):
        if monolingual:
            segment_source = table_contents[0][segment_index]
            segment_modified = table_contents[2][segment_index]
        else:
            segment_source = table_contents[1][segment_index]
            segment_modified = table_contents[2][segment_index]
        segment_source = segment_source.decode("utf-8").encode("windows-1252").decode("utf-8")
        segment_modified = segment_modified.decode("utf-8").encode("windows-1252").decode("utf-8")
        id_source = segment_index
        id_target = id_source + 100000
        final_output = '<a href='+ '"' + "javascript:showhide('" +str(id_source)+ "')" + '"' + '><input type="button" value="Source"></a>'
        final_output += '<a href='+ '"' + "javascript:showhide('" +str(id_target)+ "')" + '"' + '><input type="button" value="Target"></a>'
        final_output += '<div id="%d" style="display: none;height:200px;width:400px;border:1px solid #ccc;font:16px/26px Georgia, Garamond, Serif;overflow:auto;">%s</div>' % (id_source,segment_source)
        final_output += '<div id="%d" style="display: none;height:200px;width:400px;border:1px solid #ccc;font:16px/26px Georgia, Garamond, Serif;overflow:auto;">%s</div>' % (id_target,segment_modified)
        return final_output
    def build_table(self, percentaje_spent_by_segment):
        table_data_list = []
        for segment_index in percentaje_spent_by_segment:
            string = "<tr><td>"+str(segment_index)
            string += self.format_table_data(segment_index,self.tables["translation_table"].tables_content,self.tables["translation_table"].monolingual)+"</td>"
            string += "<td>"+str(percentaje_spent_by_segment[segment_index])+"</td></tr>"
            table_data_list.append(string)
        return ''.join(table_data_list)
    def build_pie_as_json_string(self, percentaje_spent_by_segment):
        pie_as_json_string_list = []
        for a in percentaje_spent_by_segment:
            string = '{label: "' + str(a) + '", data: ' + str(percentaje_spent_by_segment[a]) + '}'
            pie_as_json_string_list.append(string)
        return ','.join(pie_as_json_string_list)

    def calculate_statistics_event(self, button, statistics_name):
            self.saveChangedFromPostEditing()
            self.calculate_statistics(statistics_name)
            self.notebook.set_current_page(6)
    def calculate_statistics(self, statistics_name):
        pie_as_json_string = ""
        if statistics_name == "time_per_segment":
            pie_as_json_string,table_data,title = self.calculate_time_per_segment()
        elif statistics_name == "insertions":
            pie_as_json_string,table_data,title = self.calculate_insertions_per_segment()
        elif statistics_name == "deletions":
            pie_as_json_string,table_data,title = self.calculate_deletions_per_segment()
        if pie_as_json_string:
            html_injector.inject_into_html(pie_as_json_string, table_data, title, statistics_name)
            self.add_statistics(statistics_name)

    def add_statistics(self, statistic_to_show):
        self.notebook.remove_page(6)
        self.HTML_view.reload_bypass_cache()
        self.notebook.insert_page(self.HTML_view, Gtk.Label('Statistics'), 6)
        self.update_notebook()

    def addDifferencesTab(self):
        self.preparation = Gtk.VBox()
        self.notebook.remove_page(5)
        self.preparation.pack_start(self.diff_tab_grid, expand =True, fill =True, padding =0)
        self.notebook.insert_page(self.preparation, Gtk.Label('Differences'), 5)
        self.update_notebook()

    def update_notebook(self, maybe_show_buttons = False):
        self.notebook.show_all()
        if maybe_show_buttons:
            self.show_the_available_stats()

    def show_the_available_stats(self):
        #if the json string is empty, then no calculations have been made
        #and so the buttons should not be shown
        insertions =  self.calculate_insertions_per_segment()[0]
        deletions = self.calculate_deletions_per_segment()[0]
        time = self.calculate_time_per_segment()[0]

        if insertions:self.tables["translation_table"].insertions_statistics_button.show()
        else: self.tables["translation_table"].insertions_statistics_button.hide()
        if deletions:self.tables["translation_table"].deletions_statistics_button.show()
        else:self.tables["translation_table"].deletions_statistics_button.hide()
        if time:self.tables["translation_table"].time_statistics_button.show()
        else:self.tables["translation_table"].time_statistics_button.hide()


        if self.tables["translation_table"].REC_button.get_active():
            self.tables["translation_table"].save_post_editing_changes_button.hide()

    def save_not_using_git(self):
        #lets see how using closure is seen by the team... here's hope it plays out!
        def savefile(text, filename):
            text_file = open(filename, "w")
            text_file.write(text)
            text_file.close()
        savefile('\n'.join(self.tables["translation_table"].tables_content[self.tables["translation_table"].source_text_lines]), self.saved_origin_filepath)

    def save_using_log(self):
        text_lines_to_save = self.tables["translation_table"].reference_text_lines

        for index in range(0, len(self.tables["translation_table"].tables_content[text_lines_to_save])):
            if index in self.tables["translation_table"].translation_reference_text_TextViews_modified_flag:
                modified_reference = self.tables["translation_table"].translation_reference_text_TextViews_modified_flag[index]
                if modified_reference not in self.saved_modified_references:
                    self.saved_modified_references.append(modified_reference)
                    if self.last_change_timestamp not in self.log:
                        self.log[self.last_change_timestamp] = {}
                    self.log[self.last_change_timestamp][index] = modified_reference
        with open(self.source_log_filepath, 'w') as outfile:
            json.dump(self.log, outfile)


    def saveChangedFromPostEditing(self):
        self.last_change_timestamp = int(time.time() * 1000)
        #reconstruct all cells from the table of the target column
        for index in range(0, len(self.tables["translation_table"].tables_content[1])):
            if index in self.tables["translation_table"].translation_reference_text_TextViews_modified_flag:
                self.modified_references.append(self.tables["translation_table"].translation_reference_text_TextViews_modified_flag[index])
            else:
                self.modified_references.append(self.tables["translation_table"].tables_content[1][index])
        self.save_not_using_git()
        self.save_using_log()
    def preparePostEditingAnalysis(self):
        self.saveChangedFromPostEditing()
        self.diff_tab_grid = Gtk.Grid()
        self.diff_tab_grid.set_row_spacing(1)
        self.diff_tab_grid.set_column_spacing(20)
        self.tables["diff_table"] = Table("diff_table",self.post_editing_source,self.post_editing_reference, self.preparePostEditingAnalysis_event,self.preparePostEditingAnalysis, self.calculate_statistics_event, self.diff_tab_grid,self.output_directory)
        self.addDifferencesTab()

        self.tables["translation_table"].save_post_editing_changes_button.hide()
        self.show_the_available_stats()


    def preparePostEditingAnalysis_event(self, button):
        self.preparePostEditingAnalysis()

    def delete_generated_files(self):
        shutil.rmtree("./statistics/generated", ignore_errors=True)
