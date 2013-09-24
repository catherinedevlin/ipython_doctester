
"""Run doctests on a single class or function, and report for IPython Notebook.

Decorate each function or class to be tested with ``ipython_doctester.test``.

If you want to turn off automatic testing but don't want to take the @test
decorators off, set ipython_doctester.run_tests = False.

Note: It's easy to cheat by simply deleting or changing the doctest.  That's
OK, cheating is learning, too.

If you want to track students' progress through a notebook in a
classroom setting, you can; see
http://ipython-docent.appspot.com/
for instructions.

Developed for the Dayton Python Workshop:
https://openhatch.org/wiki/Dayton_Python_Workshop
catherine.devlin@gmail.com

"""

import IPython
import doctest
import cgi
import inspect
import sys
import requests


from IPython.core.displaypub import publish_display_data

try:
    from IPython.zmq import displayhook as zmq_displayhook
except ImportError:
    # zmq in kernel in Ipython 1.x serie
    # http://ipython.org/ipython-doc/rel-1.0.0/whatsnew/version1.0.html
    from IPython.kernel.zmq import displayhook as zmq_displayhook


__version__ = '0.2.2'
finder = doctest.DocTestFinder()
docent_url = 'http://ipython-docent.appspot.com'

"""Set these per session, as desired."""
run_tests = True
verbose = False    # ``True`` causes the result table to print,
                   # even for successes

"""Set these if desired to track student progress
at http://ipython-docent.appspot.com/.
See that page for more instructions."""
student_name = None
workshop_name = None


def running_from_notebook():
    return isinstance(sys.displayhook, zmq_displayhook.ZMQShellDisplayHook)


class Reporter(object):
    html = running_from_notebook()

    def __init__(self):
        self.failed = False
        self.examples = []
        self.txt = ''

    example_template = ('<tr><td><code><pre>%s</pre></code></td>'
                        '<td><pre>%s</pre></td>'
                        '<td><pre style="color:%s">%s</pre></td></tr>')
    fail_template = """
        <p><span style="color:red;">Oops!</span>  Not quite there yet...</p>
      """
    success_template = """
      <p style="color:green;font-size:250%;font-weight=bold">Success!</p>
      """

    def trap_txt(self, txt):
        self.txt += txt

    def publish(self):
        # if self.html:
        #     IPython.core.displaypub.publish_html(self._repr_html_())
        # else:
        #     IPython.core.displaypub.publish_pretty(self.txt)

        if self.html:
            publish_display_data("ipython_doctester",
                                 {'text/html': self._repr_html_()})
        else:
            publish_display_data("ipython_doctester",
                                 {'text/plain': self.txt})

    def _repr_html_(self):
        result = self.fail_template if self.failed else self.success_template
        if verbose or self.failed:
            examples = '\n        '.join(self.example_template %
                                        (cgi.escape(e.source),
                                         cgi.escape(e.want),
                                         e.color, cgi.escape(e.got)
                                         )for e in self.examples)
            result += ("""
                       <table>
                       <tr><th>Tried</th><th>Expected</th><th>Got</th></tr>"""
                       + examples + """
                      </table>
                      """)
        return result


reporter = Reporter()


class Runner(doctest.DocTestRunner):

    def _or_nothing(self, x):
        if x in (None, ''):
            return 'Nothing'
        elif hasattr(x, 'strip') and x.strip() == '':
            return '<BLANKLINE>'
        return x

    def report_failure(self, out, test, example, got):
        example.got = self._or_nothing(got)
        example.want = self._or_nothing(example.want)
        example.color = 'red'
        reporter.examples.append(example)
        reporter.failed = True
        return doctest.DocTestRunner.report_failure(self, out, test, example,
                                                    got)

    def report_success(self, out, test, example, got):
        example.got = self._or_nothing(got)
        example.want = self._or_nothing(example.want)
        example.color = 'green'
        reporter.examples.append(example)
        return doctest.DocTestRunner.report_success(self, out, test, example, got)

    def report_unexpected_exception(self, out, test, example, exc_info):
        reporter.failed = True
        trim = len(reporter.txt)
        result = doctest.DocTestRunner.report_unexpected_exception(
            self, out, test, example, exc_info)
        example.got = reporter.txt[trim:].split('Exception raised:')[1]
        example.want = self._or_nothing(example.want)
        example.color = 'red'
        reporter.examples.append(example)
        return result


runner = Runner()
finder = doctest.DocTestFinder()


class IPythonDoctesterException(Exception):

    def _repr_html_(self):
        return '<pre>\n%s\n</pre>' % self.txt


class NoTestsException(IPythonDoctesterException):
    txt = """
    OOPS!  We expected to find a doctest -
    a string immediately after the function definition, looking something like
        def do_something():
            '''
            >>> do_something()
            'did something'
            '''
    ... but it wasn't there. Did you insert code between the function definition
    and the doctest?
    """


class NoStudentNameException(IPythonDoctesterException):
    txt = """
    OOPS!  We need you to set the ipython_doctester.student_name variable;
    please look for it (probably in the first cell in this worksheet) and
    enter your name, like
        ipython_doctester.student_name = 'Catherine'
    ... then hit Shift+Enter to execute that cell, then come back here to
    execute this one.
    """


def testobj(func):
    tests = finder.find(func)
    if not tests:
        raise NoTestsException
    if workshop_name and not student_name:
        raise NoStudentNameException()
    globs = {}  # TODO: get the ipython globals?
    reporter.__init__()
    globs[func.__name__] = func
    globs['reporter'] = reporter
    for t in tests:
        t.globs = globs.copy()
        runner.run(t, out=reporter.trap_txt)
    reporter.publish()
    if workshop_name:
        payload = dict(function_name=func.__name__,
                       failure=reporter.failed,
                       source=inspect.getsource(func),
                       workshop_name=workshop_name,
                       student_name=student_name)
        requests.post(docent_url + '/record', data=payload)

    return reporter


def report_error(e):
    if running_from_notebook():
        IPython.core.displaypub.publish_html(e._repr_html_())
    else:
        IPython.core.displaypub.publish_pretty(e.txt)


def test(func):
    if run_tests:
        try:
            result = testobj(func)
        except (NoStudentNameException, NoTestsException) as e:
            report_error(e)
    return func
