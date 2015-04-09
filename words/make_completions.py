import json

completions = {
    'scope': 'source.sal',
}

function_dict = {}
reserved_set = set()


class DocLine:
    def __init__(self, declaration, doc):
        self.declaration = declaration
        self.doc = doc


def get_func_name(text):
    return text.split()[0]


def stripped_name(text):
    split = get_func_name(text)
    return split.strip("*")


def is_func(func_name):
    return count_letters(func_name) >= 2 and not "*" in func_name


def is_sal(text_line):
    return not "(" in text_line


def count_letters(text):
    return sum([int(c.isalpha()) for c in text])


def build_snippet(text):
    split_strings = text.split()
    func_name = split_strings[0]
    for i in range(1, len(split_strings)):
        param = split_strings[i]
    return None


def make_doc_data():
    words_file = open("./NyquistWords.txt")
    reserved_file = open("./SALKeywords.txt")
    completions_list = []
    # Add reserved keywords to completions
    reserved_line = reserved_file.readline()
    while reserved_line != '':
        reserved = reserved_line.strip()
        completions_list.append({"trigger": reserved,
                                 "contents": reserved})
        reserved_set.add(reserved)
        reserved_line = reserved_file.readline()

    # Add functions to completions
    func_line = words_file.readline()
    while func_line != '':
        html_line = words_file.readline()
        func_name = get_func_name(func_line)
        func_identifier = stripped_name(func_line)
        # An identifier for the function. The goal is to allow for partial identifiers
        if is_func(func_name) and is_sal(func_line) and not func_name in reserved_set:
            function_dict[func_name] = DocLine(func_line, html_line)
            function_dict[func_identifier] = DocLine(func_line, html_line)
            completions_list.append({"trigger": func_name,
                                     "contents": func_name})
        func_line = words_file.readline()
    completions['completions'] = completions_list


make_doc_data()

with open('SAL.sublime-completions', 'wb') as completions_file:
    json.dump(completions, completions_file, indent=2)
print "Done"