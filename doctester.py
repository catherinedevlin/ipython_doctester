import doctest
import sys
import contextlib
import cgi

"""Run doctests on a single class or function, and report for IPython Notebook.

Lets you create an interactive tutorial in IPython Notebook with doctests to guide
a student along.  Start the notebook with this import:

    In [1]: from doctester import test
    
In each subsequent cell, set up objects with their doctests, and with absent (or flawed)
function bodies; then include a call to test().

    In [2]: def square(x):
                '''
                >>> f(2)
                4
                '''
                
            test(square)
            
When the student evaluates the cell, she will get feedback on her solution.            

Notes: 

  - It's easy to cheat by simply not including a doctest.  The test will report success...
  
  - If your return values contain elements that look exactly like they came from a 
    docstring result - like '\nGot:\n    ' - chaos will ensue.  C'mon, be nice.
    
  - This is fragile and depends on doctest's typical output format.  If that format ever
    changes, this will need repair.
    
    Developed for the Dayton Python Workshop: https://openhatch.org/wiki/Dayton_Python_Workshop
    catherine.devlin@gmail.com
    

"""

# Thanks to StackOverflow user1200039 for the capture recipe
@contextlib.contextmanager
def capture():
    """Capture stdout as a string.
   
    Use as a context manager:
    
    with capture() as out:
        print 'hi'    
    out == 'hi'
    
    Thanks to StackOverflow user1200039 for this recipe.
    """
    from cStringIO import StringIO
    oldout,olderr = sys.stdout, sys.stderr
    try:
        out=[StringIO(), StringIO()]
        sys.stdout,sys.stderr = out
        yield out
    finally:
        sys.stdout,sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

class Failure(object):
    """A failed test case, as interpreted from doctest's output."""
    template = '<tr><td><code><pre>%s</pre></code></td><td><pre>%s</pre></td><td><pre>%s</pre></td></tr>'
    def __init__(self, raw_txt):
        self.raw_txt = raw_txt
        self.exception = False
        if '\nGot:\n    ' in raw_txt:
            (txt, self.actual) = raw_txt.split('\nGot:\n    ')
        elif '\nGot nothing\n' in raw_txt:
            (txt, self.actual) = raw_txt.split('\nGot nothing\n')
            self.actual = 'nothing (None)'
        elif '\nException raised:\n    Traceback (most recent call last):\n     ' in raw_txt:
            (txt, self.actual) = raw_txt.split('\nException raised:\n    ')
            self.actual = '\nException raised:\n    %s' % self.actual
            self.exception = True
            self.expected = ''  # not true, but doctest doesn't report the expected during exception
        self.actual = self.actual.strip()
        if not self.exception:
            (txt, self.expected) = txt.split('\nExpected:\n    ') 
        self.expected = self.expected.strip()
        (txt, self.called) = txt.split('\nFailed example:\n    ')
        self.called = self.called.strip()
    def __str__(self):
        return raw_txt
    def _repr_html_(self):
        return self.template % (cgi.escape(self.called), 
                                cgi.escape(self.expected), 
                                cgi.escape(self.actual))

    
class AllTestsResult(object):
    """Results of running the doctests on a single function or class."""
    fail_template = """
      <p><span style="color:red;">Oops!</span>  Not quite there yet...</p>
      <table>
        <tr><th>Tried</th><th>Expected</th><th>Got</th></tr>
        %s
      </table>
      """
    success_template = """
      <p style="color:green;font-size:250%;font-weight=bold">Success!</p>
      """
    def __init__(self, captured_list):
        self.failures = []
        self.rawtxt = captured_list[0]
        raw_failures = self.rawtxt.split('**********************************************************************')
        for raw_failure in raw_failures:
            if raw_failure:
                self.failures.append(Failure(raw_failure))
    def __str__(self):
        return self.rawtxt
    def _repr_html_(self):
        """Called by ipython notebook to represent result in page."""
        if self.failures:
            result = self.fail_template % '\n        '.join(f._repr_html_() for f in self.failures)
        else:
            result = self.success_template
        return result
       
def test(func):
    with capture() as result:
        doctest.run_docstring_examples(func, {func.__name__: func})
    return AllTestsResult(result)