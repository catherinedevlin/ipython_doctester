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
  
    Developed for the Dayton Python Workshop: https://openhatch.org/wiki/Dayton_Python_Workshop
    catherine.devlin@gmail.com
    

"""

finder = doctest.DocTestFinder()

class Reporter(object):
    def __init__(self):
        self.failed = False
        self.examples = []
        self.txt = ''
    fail_template = """
      <p><span style="color:red;">Oops!</span>  Not quite there yet...</p>
      <table>
        <tr><th>Tried</th><th>Expected</th><th>Got</th></tr>
        %s
      </table>
      """
    example_template = '<tr><td><code><pre>%s</pre></code></td><td><pre>%s</pre></td><td><pre>%s</pre></td></tr>'
    success_template = """
      <p style="color:green;font-size:250%;font-weight=bold">Success!</p>
      """    
    def out(self, txt):
        self.txt = self.txt + txt
        return txt
    def __str__(self):
        return self.txt
    def _repr_html_(self):
        if self.failed:
            examples = '\n        '.join(self.example_template % 
                                 (cgi.escape(e.source), cgi.escape(e.want), 
                                  cgi.escape(e.got)
                                  )for e in self.examples)
            result = """
        <p><span style="color:red;">Oops!</span>  Not quite there yet...</p>
        <table>
          <tr><th>Tried</th><th>Expected</th><th>Got</th></tr>""" + examples + """
        </table>
        """
        else:
            result = self.success_template
        return result
        
reporter = Reporter()

class Runner(doctest.DocTestRunner):
    def report_failure(self, out, test, example, got):
        example.got = got
        reporter.examples.append(example)
        reporter.failed = True
        return doctest.DocTestRunner.report_failure(self, out, test, example, got)
    def report_success(self, out, test, example, got):
        example.got = got 
        reporter.examples.append(example)
        return doctest.DocTestRunner.report_success(self, out, test, example, got)    
    def report_unexpected_exception(self, out, test, example, exc_info):
        reporter.examples.append(example)
        reporter.failed = True
        trim = len(reporter.txt)
        result = doctest.DocTestRunner.report_unexpected_exception(self, out, test, example, exc_info)
        example.got = reporter.txt[trim:].split('Exception raised:')[1]
        return result
         
        
runner = Runner()
finder = doctest.DocTestFinder()

"""
? - possible approach ?
def result_display(self, arg):
    if hasattr(arg, '_repr_html_'):
        '''http://osdir.com/ml/python.ipython.user/2006-06/msg00065.html '''
"""
        
def test(func):
    tests = finder.find(func)
    globs = {} # globals() # TODO: get the ipython globals?
    reporter.__init__()
    globs[func.__name__] = func
    globs['reporter'] = reporter
    for t in tests:
        t.globs = globs
        runner.run(t, out=reporter.out)
    func._repr_html_ = reporter._repr_html_            
    return reporter

def test_me(func):
    result = test(func)
    # print result - this displays the plaintext result
    func._repr_html_ = result._repr_html_
    return func

