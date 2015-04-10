from HTMLParser import HTMLParser
import json
import re


class DocBuilder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.results = {}
        self.dl_block = False
        self.dd_block = False
        self.dt_block = False
        self.code_block = False

        self.buffer = ""
        self.dt_data = ""

    def handle_starttag(self, tag, attrs):
        if tag == "dl":
            self.dl_block += 1
        if tag == "dd" and self.dl_block == 1:
            self.buf_reset()
            self.dd_block = True
            self.dt_block = False
            self.code_block = False
        if tag == "dt" and self.dl_block == 1:
            self.buf_reset()
            self.dt_block = True
            self.dd_block = False
            self.code_block = False
        if tag == "code" and self.dl_block > 0:
            self.code_block = True

        if tag == "br":
            self.buffer += ", "

    def buf_reset(self):
        if self.dt_block:
            self.dt_data = re.sub(r'(\[SAL\]|\[LISP\]).*', r'\1', self.buffer).strip()

        if self.dd_block:
            dd_data = re.sub(r'(\[SAL\]|\[LISP\]).*', r'\1', self.buffer).strip()
            entry = make_entry(self.dt_data, dd_data)
            if entry:
                (name, value) = entry
                self.results[name] = value

        self.buffer = ""

    def handle_endtag(self, tag):
        if tag == "dl":
            self.dl_block -= 1
            if self.dl_block == 0:
                self.buf_reset()
                self.dt_block = False
                self.dd_block = False
                self.dl_block = False
        if tag == "dd":
            self.dd_block = False
            self.buf_reset()
        if tag == "dt":
            self.dt_block = False
            self.buf_reset()
        if tag == "code":
            self.code_block = False
        if tag == "p":
            self.buf_reset()
            self.dt_block = False
            self.dd_block = False

    def handle_data(self, data):

        if self.dt_block:
            data = data.replace("\n", "")
            self.buffer += data

        if self.dd_block:
            data = data.replace("\n", " ")
            self.buffer += data


def clean_description(description):
    description = description.strip(", ")
    description = re.sub("\s+", " ", description)
    description = re.sub(",+", ",", description)
    return description


def make_parameters(text):
    text = re.sub(r"([\[\]])", r" \1 ", text)
    return re.sub("[\(\),]", " ", text).strip().split()


def make_entry(function, description):
    sal = "[SAL]" in function
    text = function.replace("[SAL]", "").replace("[LISP]", "")
    is_function = not re.search("(\[SAL\]|\[LISP\])", function) is None
    is_var = not re.match("\*.*\*", function) is None

    params = make_parameters(text)
    name = params[0]
    tokens = params

    description = clean_description(description)
    if is_function or is_var:
        return (name, {'declaration': text.strip(),
                       'sal': sal,
                       'tokens': tokens,
                       'is_function': is_function,
                       'name': name, "description": description})
    else:
        return None



def make_docs():
    res = {}
    for count in range(8, 20):
        f = open("./docs/part" + str(count) + ".html")
        text = f.read()
        builder = DocBuilder()
        builder.feed(text)
        f.close()
        res.update(builder.results)
    return res


results = make_docs()

with open('docs.json', 'wb') as docs:
    json.dump(results, docs, indent=4)
print "Done"