
def build_run(filename):
    compiled_text = ""
    with open("lisp/run.lsp") as compiler:
        line = compiler.readline()
        while line != '':
            compiled_text += line
            line = compiler.readline()
    compiled_text = compiled_text.format(SAL_FILE=filename)
    return compiled_text

