# noinspection PyUnresolvedReferences
import os
import threading
import subprocess
import functools
import collections
import time
import sys

import sublime_plugin
import sublime


def sublime3():
    return sys.version_info >= (3, 0)


if sublime3():
    from .terminal import sal_build

    class DataListener(object):
        def on_data(self, proc, data):
            pass

        def on_finished(self, proc):
            pass

    class AsyncProcess(object):
        # noinspection PyUnboundLocalVariable

        def __init__(self, cmd, listener):
            self.listener = listener
            self.killed = False

            startupinfo = None
            if os.name == "nt":  # If windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            env = os.environ.copy()
            for k, v in env.items():
                env[k] = os.path.expandvars(v)
            self.proc = subprocess.Popen(cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         startupinfo=startupinfo,
                                         env=env)

            if self.proc.stdout:
                threading.Thread(target=self.read_stream, args=(self.proc.stdout,), kwargs={'finish': True}).start()

        def kill(self):
            if not self.killed:
                self.killed = True
                time.sleep(.25)
                self.proc.kill()
                self.listener = None

        def poll(self):
            return self.proc.poll() is None

        def read_stream(self, stream, finish=False):
            fd = os.fdopen(stream.fileno())
            while True:
                data = fd.readline()

                if len(data) > 0:
                    if self.listener:
                        self.listener.on_data(self, data)
                else:
                    stream.close()

                    if self.listener and finish:
                        self.listener.on_finished(self)
                    break

    # noinspection PyAttributeOutsideInit
    class SalExecCommand(sublime_plugin.WindowCommand, DataListener):
        BLOCK_SIZE = 2 ** 14
        text_queue = collections.deque()
        text_queue_proc = None
        text_queue_lock = threading.Lock()

        proc = None

        def run(self,
                cmd=None,
                file_regex="",
                line_regex="",
                working_dir="",
                word_wrap=True,
                syntax="Packages/Text/Plain text.tmLanguage"):
            self.cmd = cmd
            self.text_queue_lock.acquire()
            try:
                self.output_content = False
                self.text_queue.clear()
                self.text_queue_proc = None
            finally:
                self.text_queue_lock.release()

            if self.proc:
                self.proc.kill()
                self.proc = None
                self.append_string(None, "[Cancelled Build]")
                return

            if not hasattr(self, 'output_view'):
                self.output_view = self.window.create_output_panel("exec")

            if working_dir == "" and self.window.active_view() \
                    and self.window.active_view().file_name():
                working_dir = os.path.dirname(self.window.active_view().file_name())

            self.output_view.settings().set("result_file_regex", file_regex)
            self.output_view.settings().set("result_line_regex", line_regex)
            self.output_view.settings().set("result_base_dir", working_dir)
            self.output_view.settings().set("word_wrap", word_wrap)
            self.output_view.settings().set("line_numbers", False)
            self.output_view.settings().set("gutter", False)
            self.output_view.settings().set("scroll_past_end", False)
            self.output_view.assign_syntax(syntax)

            self.window.create_output_panel("exec")
            self.proc = None
            sublime.status_message("Building")

            show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
            if show_panel_on_build:
                self.window.run_command("show_panel", {"panel": "output.exec"})

            if working_dir != "":
                os.chdir(working_dir)
            tmp_file_text = sal_build.build_run(cmd, working_dir)
            self.tmp_file_name = cmd + ".tmp~"
            f = open(self.tmp_file_name, "w+")
            f.write(tmp_file_text)
            f.close()

            try:
                self.proc = AsyncProcess(["nyquist", "-t", self.tmp_file_name], self)
                self.text_queue_lock.acquire()
                try:
                    self.text_queue_proc = self.proc
                finally:
                    self.text_queue_lock.release()
            except Exception as e:
                self.append_string(None, str(e) + "\n")
                self.append_string(None, "[Finished]")

        def is_enabled(self, kill=False):
            if kill:
                return (self.proc is not None) and self.proc.poll()
            else:
                return True

        def append_string(self, proc, data_str):
            self.text_queue_lock.acquire()

            line = data_str.rstrip()
            if line == '\"SUBLIME.SENTINEL\"' or line == ">":
                self.text_queue_lock.release()
                return
            was_empty = False
            try:
                if proc != self.text_queue_proc:
                    if proc:
                        proc.kill()
                    return

                if len(self.text_queue) == 0:
                    was_empty = True
                    self.text_queue.append("")

                available = self.BLOCK_SIZE - len(self.text_queue[-1])

                if len(line) > 0 and line[0] == ';':
                    self.output_content = True
                    data_str = "Running " + self.cmd + " \n\n"

                if self.output_content:
                    if len(data_str) < available:
                        cur = self.text_queue.pop()
                        self.text_queue.append(cur + data_str)
                    else:
                        self.text_queue.append(data_str)


            finally:
                self.text_queue_lock.release()

            if was_empty:
                sublime.set_timeout(self.service_text_queue, 0)

        def service_text_queue(self):
            self.text_queue_lock.acquire()

            try:
                if len(self.text_queue) == 0:
                    return

                text_str = self.text_queue.popleft()
                is_empty = (len(self.text_queue) == 0)
            finally:
                self.text_queue_lock.release()

            self.output_view.run_command('append', {'characters': text_str, 'force': True, 'scroll_to_end': True})

            if not is_empty:
                sublime.set_timeout(self.service_text_queue, 1)

        def finish(self, proc):
            self.append_string(proc, "\n[Done]")

            if proc != self.proc:
                return

            errs = self.output_view.find_all_results()
            if len(errs) == 0:
                sublime.status_message("Build finished")
            else:
                sublime.status_message("Build finished with %d errors" % len(errs))

        def on_data(self, proc, data):
            # data_str = data.decode("utf-8")
            data_str = data
            data_str = data_str.replace('\r\n', '\n').replace('\r', '\n')
            self.append_string(proc, data_str)

        def on_finished(self, proc):
            #Called from the async process, so can't run immediately.
            sublime.set_timeout(functools.partial(self.finish, proc), 0)
            os.remove(self.tmp_file_name)
            self.proc = None
