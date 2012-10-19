import doctest
import cgi
import IPython.core.display

"""Run doctests on a single class or function, and report for IPython Notebook.

Lets you create an interactive tutorial in IPython Notebook with doctests to guide
a student along.  Start the notebook with this import:

    In [1]: from doctester import test
    
In each subsequent cell, set up objects with their doctests, and with absent (or flawed)
function bodies, and decorate them with @test_html (or @test if you want plain text,
such as if you're not in the IPython Notebook).

    In [2]: @test_html
            def square(x):
                '''
                >>> f(2)
                4
                '''
            
When the student evaluates the cell, she will get feedback on her solution.            

Notes: 

  - It's easy to cheat by simply not including a doctest.  The test will report success...
  
  - Still hoping to find a way for @test to automatically detect it's being run from
    the Notebook and publish HTML output accordingly.
  
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
    def trap_txt(self, txt):
        self.txt += txt
    def publish(self, html):
        if html:
            IPython.core.display.publish_html(self._repr_html_())
        else:
            IPython.core.display.publish_pretty(self.txt)
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
        reporter.failed = True
        trim = len(reporter.txt)
        result = doctest.DocTestRunner.report_unexpected_exception(self, out, test, example, exc_info)
        example.got = reporter.txt[trim:].split('Exception raised:')[1]
        reporter.examples.append(example)
        return result
         
        
runner = Runner()
finder = doctest.DocTestFinder()

def testobj(func, html=False):
    tests = finder.find(func)
    globs = {} # globals() # TODO: get the ipython globals?
    reporter.__init__()
    globs[func.__name__] = func
    globs['reporter'] = reporter
    for t in tests:
        t.globs = globs
        runner.run(t, out=reporter.trap_txt)
        reporter.publish(html)
    return reporter

def test(func):
    result = testobj(func, html=False)
    return func

def test_html(func):
    result = testobj(func, html=True)
    return func
