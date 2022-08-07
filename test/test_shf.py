# The integration test of shf
# Inspired by skim's integration test: https://github.com/lotabout/skim/blob/master/test/test_skim.py

import inspect
import os
import re
import shutil
import subprocess
import time
import unittest

INPUT_RECORD_SEPARATOR = "\n"
DEFAULT_TIMEOUT = 3000

SCRIPT_PATH = os.path.realpath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
BASE = os.path.expanduser(os.path.join(SCRIPT_DIR, ".."))
SHF = f"{BASE}/target/release/shf"

os.chdir(BASE)


def now_mills():
    return int(round(time.time() * 1000))


def wait(func, timeout_handler=None):
    since = now_mills()
    while now_mills() - since < DEFAULT_TIMEOUT:
        time.sleep(0.05)
        ret = func()
        if ret is not None and ret:
            return
    if timeout_handler is not None:
        timeout_handler()
    raise TimeoutError("Timeout on wait")


class Shell:
    """The shell configurations for tmux tests"""

    @staticmethod
    def bash():
        return "PS1= PROMPT_COMMAND= bash --rcfile None"

    @staticmethod
    def zsh():
        return "PS1= PROMPT_COMMAND= HISTSIZE=100 zsh -f"

    @staticmethod
    def fish():
        return "fish -N --init-command='function fish_prompt; end'"


class Key:
    """Represent a key to send to tmux"""

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return self.key


class Ctrl(Key):
    """Represent a control key"""

    def __init__(self, key):
        super(Ctrl, self).__init__(key)

    def __repr__(self):
        return f"C-{self.key.upper()}"


class Alt(Key):
    """Represent an alt key"""

    def __init__(self, key):
        super(Alt, self).__init__(key)

    def __repr__(self):
        return f"M-{self.key}"


class TmuxOutput(list):
    """A list that contains the output of tmux"""

    # match the status line
    # normal:  `| 10/219 [2]               8/0.`
    # inline:  `> query < 10/219 [2]       8/0.`
    # preview: `> query < 10/219 [2]       8/0.│...`
    RE = re.compile(
        r"(?:^|[^<-]*). ([0-9]+)/([0-9]+)(?:/[A-Z]*)?(?: \[([0-9]+)\])? *([0-9]+)/(-?[0-9]+)(\.)?(?: │)? *$"
    )

    def __init__(self, iteratable=[]):
        super(TmuxOutput, self).__init__(iteratable)
        self._counts = None

    def counts(self):
        if self._counts is not None:
            return self._counts

        # match_count item_count select_count item_cursor matcher_stopped
        ret = (0, 0, 0, 0, 0, ".")
        for line in self:
            mat = TmuxOutput.RE.match(line)
            if mat is not None:
                ret = mat.groups()
                break
        self._counts = ret
        return ret

    def match_count(self):
        count = self.counts()[0]
        return int(count) if count is not None else None

    def item_count(self):
        count = self.counts()[1]
        return int(count) if count is not None else None

    def select_count(self):
        count = self.counts()[2]
        return int(count) if count is not None else None

    def item_index(self):
        count = self.counts()[3]
        return int(count) if count is not None else None

    def hscroll(self):
        count = self.counts()[4]
        return int(count) if count is not None else None

    def matcher_stopped(self):
        return self.counts()[5] != "."

    def ready_with_lines(self, lines):
        return self.item_count() == lines and self.matcher_stopped()

    def ready_with_matches(self, matches):
        return self.match_count() == matches and self.matcher_stopped()

    def any_include(self, val):
        if hasattr(re, "_pattern_type") and isinstance(val, re._pattern_type):
            method = lambda l: val.match(l)
        if hasattr(re, "Pattern") and isinstance(val, re.Pattern):
            method = lambda l: val.match(l)
        else:
            method = lambda l: l.find(val) >= 0
        for line in self:
            if method(line):
                return True
        return False


class Tmux(object):
    TEMPNAME = "/tmp/shf-test.txt"

    """Object to manipulate tmux and get result"""

    def __init__(self, shell="bash"):
        super(Tmux, self).__init__()

        if shell == "bash":
            shell_cmd = Shell.bash()
        elif shell == "zsh":
            shell_cmd = Shell.zsh()
        elif shell == "fish":
            shell_cmd = Shell.fish()
        else:
            raise ValueError(f"Unknown shell: {shell}")

        self.win = self._go("new-window", "-d", "-P", "-F", "#I", f"{shell_cmd}")[0]
        self._go("set-window-option", "-t", f"{self.win}", "pane-base-index", "0")
        self.lines = int(
            subprocess.check_output("tput lines", shell=True).decode("utf8").strip()
        )

    def _go(self, *args, **kwargs):
        """Run tmux command and return result in list of strings (lines)

        :returns: List<String>
        """
        ret = subprocess.check_output(["tmux"] + list(args))
        return ret.decode("utf8").split(INPUT_RECORD_SEPARATOR)

    def kill(self):
        self._go("kill-window", "-t", f"{self.win}", stderr=subprocess.DEVNULL)

    def send_keys(self, *args, pane=None):
        if pane is not None:
            self._go("select-window", "-t", f"{self.win}")
            target = "{self.win}.{pane}"
        else:
            target = self.win

        for key in args:
            if key is None:
                continue
            else:
                self._go("send-keys", "-t", f"{target}", f"{key}")
            time.sleep(0.01)

    def paste(self, content):
        subprocess.run(
            [
                "tmux",
                "setb",
                f"{content}",
                ";",
                "pasteb",
                "-t",
                f"{self.win}",
                ";",
                "send-keys",
                "-t",
                f"{self.win}",
                "Enter",
            ]
        )

    def capture(self, pane=0):
        def save_capture():
            try:
                self._go(
                    "capture-pane",
                    "-t",
                    f"{self.win}.{pane}",
                    stderr=subprocess.DEVNULL,
                )
                self._go("save-buffer", f"{Tmux.TEMPNAME}", stderr=subprocess.DEVNULL)
                return True
            except subprocess.CalledProcessError as ex:
                return False

        if os.path.exists(Tmux.TEMPNAME):
            os.remove(Tmux.TEMPNAME)

        wait(save_capture)
        with open(Tmux.TEMPNAME) as fp:
            content = fp.read()
            return TmuxOutput(content.rstrip().split(INPUT_RECORD_SEPARATOR))

    def until(self, predicate, refresh=False, pane=0, debug_info=None):
        def wait_callback():
            lines = self.capture()
            pred = predicate(lines)
            if pred:
                self.send_keys(Ctrl("l") if refresh else None)
            return pred

        def timeout_handler():
            lines = self.capture()
            print(lines)
            if debug_info:
                print(debug_info)

        wait(wait_callback, timeout_handler)

    def prepare(self):
        try:
            self.send_keys(Ctrl("u"), Key("hello"))
            self.until(lambda lines: lines[-1].endswith("hello"))
        except Exception as e:
            raise e
        self.send_keys(Ctrl("u"))


class TestBase(unittest.TestCase):
    TEMPNAME = "/tmp/output"

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._temp_suffix = 0

    def tempname(self):
        curframe = inspect.currentframe()
        frames = inspect.getouterframes(curframe)

        names = [f.function for f in frames if f.function.startswith("test_")]
        fun_name = names[0] if len(names) > 0 else "test"

        return "-".join((TestBase.TEMPNAME, fun_name, str(self._temp_suffix)))

    def writelines(self, path, lines):
        if os.path.exists(path):
            os.remove(path)

        with open(path, "w") as fp:
            fp.writelines(lines)

    def readonce(self):
        path = self.tempname()
        try:
            wait(lambda: os.path.exists(path))
            with open(path) as fp:
                return fp.read()
        finally:
            if os.path.exists(path):
                os.remove(path)
            self._temp_suffix += 1
            self.tmux.prepare()

    def shf(self, *opts):
        tmp = self.tempname()
        return f"{SHF} {' '.join(map(str, opts))} > {tmp}.tmp; mv {tmp}.tmp {tmp}"

    def command_until(
        self, until_predicate, shf_options, stdin="echo -e 'a1\\na2\\na3'"
    ):
        command_keys = stdin + " | " + self.shf(*shf_options)
        self.tmux.send_keys(command_keys)
        self.tmux.send_keys(Key("Enter"))
        self.tmux.until(until_predicate, debug_info="shf args: {}".format(shf_options))
        self.tmux.send_keys(Key("Enter"))


class TestShfBash(TestBase):
    SHELL = "bash"
    CONFIG = "/tmp/config"

    def setUp(self):
        self.tmux = Tmux(shell=self.SHELL)

    def tearDown(self):
        self.tmux.send_keys(f"rm -f {self.CONFIG}")
        self.tmux.kill()

    def test_non_existent_config(self):
        non_existent_config = "/tmp/conf"
        self.tmux.send_keys(f"{SHF} -c {non_existent_config}", Key("Enter"))
        self.tmux.until(
            lambda lines: lines[-1] == f"Error: Failed to read `{non_existent_config}`."
        )

    def test_no_valid_host_found(self):
        shutil.copy(
            f"{SCRIPT_DIR}/datafiles/config/single_wildcard_host",
            self.CONFIG,
        )
        self.tmux.send_keys(
            f"{SHF} -c {self.CONFIG}",
            Key("Enter"),
        )
        self.tmux.until(
            lambda lines: lines[-1]
            == f"Warning: No non-wildcard hosts were found in `{self.CONFIG}`."
        )

    def test_invalid_config(self):
        shutil.copy(
            f"{SCRIPT_DIR}/datafiles/config/invalid_config",
            self.CONFIG,
        )
        self.tmux.send_keys(
            f"{SHF} -c {self.CONFIG}",
            Key("Enter"),
        )
        expected_line = "Error: SSH configuration contains the following errors:"
        self.tmux.until(lambda lines: lines[-3] == expected_line)

    def test_find_host(self):
        shutil.copy(
            f"{SCRIPT_DIR}/datafiles/config/valid_config",
            self.CONFIG,
        )
        self.tmux.send_keys(
            f"{SHF} -c {self.CONFIG}",
            Key("Enter"),
        )
        self.tmux.until(lambda lines: lines[-1].startswith(">"))

        # find and select acme-dev-01
        self.tmux.send_keys("ad1")
        lines = self.tmux.capture()
        self.assertEqual("> acme-dev-01", lines[-3])
        self.tmux.send_keys(Key("Enter"))
        self.tmux.until(lambda lines: lines[-1] == "acme-dev-01")

    def test_list(self):
        shutil.copy(
            f"{SCRIPT_DIR}/datafiles/config/valid_config",
            self.CONFIG,
        )
        self.tmux.send_keys(
            f"{SHF} -c {self.CONFIG} -l",
            Key("Enter"),
        )
        self.tmux.until(lambda lines: lines[-1] == "choam-prd-02")
        lines = self.tmux.capture()
        self.assertEqual(
            lines[-6:],
            [
                "jmp-dev",
                "jmp-prd",
                "acme-dev-01",
                "acme-dev-02",
                "choam-prd-01",
                "choam-prd-02",
            ],
        )

    def test_version(self):
        self.tmux.send_keys(
            f"{SHF} -V",
            Key("Enter"),
        )
        self.tmux.until(lambda lines: lines[-1].startswith("shf"))

    def test_help(self):
        self.tmux.send_keys(
            f"{SHF} -h",
            Key("Enter"),
        )
        self.tmux.until(lambda lines: "Print version information" in lines[-1])

    def test_abort(self):
        shutil.copy(
            f"{SCRIPT_DIR}/datafiles/config/valid_config",
            self.CONFIG,
        )
        self.tmux.send_keys(
            f"{SHF} -c {self.CONFIG}",
            Key("Enter"),
        )
        self.tmux.until(lambda lines: lines[-1].startswith(">"))
        self.tmux.send_keys(Ctrl("c"))  # abort
        # the last line should be the shf command ending with /config
        self.tmux.until(lambda lines: lines[-1].endswith("/config"))


class TestShfZsh(TestShfBash):
    SHELL = "zsh"


class TestShfFish(TestShfBash):
    SHELL = "fish"


if __name__ == "__main__":
    unittest.main()
