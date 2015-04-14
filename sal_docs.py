from collections import OrderedDict
import json
import re
import webbrowser

import sublime
import sublime_plugin


class DocumentationInfo:
    def __init__(self):
        pass

    docs = None
    doc_lines = None
    dict = None
    completion_data = None
    loaded = False

    @staticmethod
    def load():
        if DocumentationInfo.loaded:
            return
        loaded = json.loads(sublime.load_resource('Packages/SALSyntax/{0}'.format("sal_info/docs.json")))
        loaded = OrderedDict(sorted(loaded.items(), key=lambda t: t[0]))
        docs = []
        lines = []
        for key, value in loaded.items():
            docs.append(value)
            lines.append([key + "\t" + language(value["sal"], value['is_function']),
                          value['declaration'],
                          shorten(value['description'])])

        DocumentationInfo.dict = loaded
        DocumentationInfo.doc_lines = lines
        DocumentationInfo.docs = docs

        DocumentationInfo.completion_data = json.loads(
            sublime.load_resource('Packages/SALSyntax/{0}'.format("sal_info/SAL.sublime-completions")))['completions']

        loaded = True


class SalDocCommand(sublime_plugin.WindowCommand):
    def run(self):

        DocumentationInfo.load()

        word_line_begin = None
        word_line_end = None
        view = self.window.active_view()

        context = self.window.extract_variables()
        if not context['file_extension'] == 'sal':
            return

        for region in view.sel():
            region_start = region.a
            region_end = region.b
            line_region = view.line(region)
            line_start = line_region.a
            line_end = line_region.b

            word_line_begin = view.substr(view.word(sublime.Region(line_start, region_end)))
            word_line_end = view.substr(view.word(sublime.Region(region_end, line_end)))

        begin_words = re.split("[\s()*]", word_line_begin)
        end_words = re.split("[\s()*]", word_line_end)
        begin_word = begin_words[-1]
        end_word = end_words[0]

        word = begin_word
        if "-" in end_word:
            word += re.sub(r"[^-]*-", "-", end_word, count=1)


        print(word)
        def on_done(val):
            if val > 0:
                item = DocumentationInfo.docs[val]
                name = item['name'].replace("*", "")
                for completion in DocumentationInfo.completion_data:
                    print(completion)
                    trigger = re.sub(r'\t.*', r'', completion['trigger'])
                    if trigger == name:
                        if 'location' in completion:
                            webbrowser.open_new_tab("http://www.cs.cmu.edu/~rbd/doc/nyquist/" + completion['location'])
                        break

            return val

        if DocumentationInfo.docs:
            index = 0
            count = 0
            for k in DocumentationInfo.docs:
                if k['name'].replace("*", "").lower() == word.lower():
                    index = count
                count += 1
            self.window.show_quick_panel(DocumentationInfo.doc_lines, on_done, 0, index)


def shorten(descr):
    if len(descr) < 100:
        return descr
    else:
        return descr[0:96] + " ..."


def language(is_sal, is_function):
    if not is_function:
        return ""
    elif is_sal:
        return "[SAL]"
    else:
        return "[LISP]"



