"""Run browser acceptance against an ephemeral localhost server of docs/ only."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import sys
from threading import Thread
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass


if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT/'docs')))
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    os.environ['HISTORIOGRAPHY_SITE_URL']=f'http://127.0.0.1:{server.server_port}/'
    try:
        suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:] or ['tests.test_site_browser','tests.test_student_beta_browser','tests.test_indigenous_browser'])
        result=unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    sys.exit(not result.wasSuccessful())
