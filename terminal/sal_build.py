import sublime


def load(name):
    return sublime.load_resource('Packages/SALSyntax/{0}'.format(name))


def escape_slashes(directory):
    return directory.replace("\\", "\\\\")


def build_run(filename, working_dir):
    compiled_text = load("lisp/run.lsp")
    compiled_text = compiled_text.format(SAL_FILE=escape_slashes(filename), WORKING_DIR=escape_slashes(working_dir))
    return compiled_text

