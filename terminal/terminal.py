import subprocess
import sublime

def run_terminal(sal_file, compile_sal=False):
    proc = subprocess.Popen(['nyquist', '-t', sal_file], stdout=subprocess.PIPE)

    content_start = False

    for line in iter(proc.stdout.readline, ''):
        line = line.rstrip()
        if line == '\"SUBLIME.SENTINEL\"':
            break
        if content_start:
            print line
        if len(line) > 0 and line[0] == ';':
            content_start = True

    proc.kill()