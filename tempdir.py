# -*- coding: utf-8 -*-

import shutil
import tempfile


class TempDir(object):
    def __init__(self, *args, **kwargs):
        self.tmpdir = tempfile.mkdtemp(*args)
        self.delete = kwargs.get("delete", True)

    def __enter__(self):
        return self.tmpdir

    def __exit__(self, type, value, traceback):
        if self.delete:
            shutil.rmtree(self.tmpdir)

