import sublime

def load(name):
    return sublime.load_resource('Packages/SAL/{0}'.format(name))
def dir(str):
    return str.replace("\\", "\\\\")

def build_run(filename):
    compiled_text = load("lisp/run.lsp")
    compiled_text = compiled_text.format(SAL_FILE=dir(filename))
    return compiled_text

