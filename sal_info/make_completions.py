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


def is_global(name):
    return "*" in name


def count_letters(text):
    return sum([int(c.isalpha()) for c in text])


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


def make_doc_data():
    words_file = open("./data/NyquistWords.txt")
    reserved_file = open("./data/SALKeywords.txt")
    custom_file = open("./data/custom_completions.json")

    completions_list = json.loads(custom_file.read(), object_hook=_decode_dict)
    # Add reserved keywords to completions
    reserved_line = reserved_file.readline()
    while reserved_line != '':
        reserved = reserved_line.strip()
        completions_list.append({"trigger": reserved + "\tkeyword",
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
            completions_list.append({"trigger": func_name + "\tfunction",
                                     "contents": func_name,
                                     "location": html_line})
        if is_global(func_name) and is_sal(func_line):
            completions_list.append({"trigger": func_name.replace("*", "") + "\tglobal",
                                     "contents": func_name,
                                     "location": html_line})
        func_line = words_file.readline()
    completions['completions'] = completions_list


make_doc_data()

with open('SAL.sublime-completions', 'wb') as completions_file:
    json.dump(completions, completions_file, indent=4)
print "Done"