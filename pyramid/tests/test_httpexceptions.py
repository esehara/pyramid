import unittest

class Test_responsecode(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from pyramid.httpexceptions import responsecode
        return responsecode(*arg, **kw)

    def test_status_404(self):
        from pyramid.httpexceptions import HTTPNotFound
        self.assertEqual(self._callFUT(404).__class__, HTTPNotFound)

    def test_status_201(self):
        from pyramid.httpexceptions import HTTPCreated
        self.assertEqual(self._callFUT(201).__class__, HTTPCreated)

    def test_extra_kw(self):
        resp = self._callFUT(404,  headers=[('abc', 'def')])
        self.assertEqual(resp.headers['abc'], 'def')
        
class Test_default_exceptionresponse_view(unittest.TestCase):
    def _callFUT(self, context, request):
        from pyramid.httpexceptions import default_exceptionresponse_view
        return default_exceptionresponse_view(context, request)

    def test_call_with_exception(self):
        context = Exception()
        result = self._callFUT(context, None)
        self.assertEqual(result, context)

    def test_call_with_nonexception(self):
        request = DummyRequest()
        context = Exception()
        request.exception = context
        result = self._callFUT(None, request)
        self.assertEqual(result, context)

class Test__no_escape(unittest.TestCase):
    def _callFUT(self, val):
        from pyramid.httpexceptions import _no_escape
        return _no_escape(val)

    def test_null(self):
        self.assertEqual(self._callFUT(None), '')

    def test_not_basestring(self):
        self.assertEqual(self._callFUT(42), '42')

    def test_unicode(self):
        class DummyUnicodeObject(object):
            def __unicode__(self):
                return u'42'
        duo = DummyUnicodeObject()
        self.assertEqual(self._callFUT(duo), u'42')

class TestWSGIHTTPException(unittest.TestCase):
    def _getTargetClass(self):
        from pyramid.httpexceptions import WSGIHTTPException
        return WSGIHTTPException

    def _getTargetSubclass(self, code='200', title='OK',
                           explanation='explanation', empty_body=False):
        cls = self._getTargetClass()
        class Subclass(cls):
            pass
        Subclass.empty_body = empty_body
        Subclass.code = code
        Subclass.title = title
        Subclass.explanation = explanation
        return Subclass

    def _makeOne(self, *arg, **kw):
        cls = self._getTargetClass()
        return cls(*arg, **kw)

    def test_implements_IResponse(self):
        from pyramid.interfaces import IResponse
        cls = self._getTargetClass()
        self.failUnless(IResponse.implementedBy(cls))

    def test_provides_IResponse(self):
        from pyramid.interfaces import IResponse
        inst = self._getTargetClass()()
        self.failUnless(IResponse.providedBy(inst))

    def test_implements_IExceptionResponse(self):
        from pyramid.interfaces import IExceptionResponse
        cls = self._getTargetClass()
        self.failUnless(IExceptionResponse.implementedBy(cls))

    def test_provides_IExceptionResponse(self):
        from pyramid.interfaces import IExceptionResponse
        inst = self._getTargetClass()()
        self.failUnless(IExceptionResponse.providedBy(inst))

    def test_ctor_sets_detail(self):
        exc = self._makeOne('message')
        self.assertEqual(exc.detail, 'message')

    def test_ctor_sets_comment(self):
        exc = self._makeOne(comment='comment')
        self.assertEqual(exc.comment, 'comment')

    def test_ctor_calls_Exception_ctor(self):
        exc = self._makeOne('message')
        self.assertEqual(exc.message, 'message')

    def test_ctor_calls_Response_ctor(self):
        exc = self._makeOne('message')
        self.assertEqual(exc.status, 'None None')

    def test_ctor_extends_headers(self):
        exc = self._makeOne(headers=[('X-Foo', 'foo')])
        self.assertEqual(exc.headers.get('X-Foo'), 'foo')

    def test_ctor_sets_body_template_obj(self):
        exc = self._makeOne(body_template='${foo}')
        self.assertEqual(
            exc.body_template_obj.substitute({'foo':'foo'}), 'foo')

    def test_ctor_with_empty_body(self):
        cls = self._getTargetSubclass(empty_body=True)
        exc = cls()
        self.assertEqual(exc.content_type, None)
        self.assertEqual(exc.content_length, None)

    def test_ctor_with_body_doesnt_set_default_app_iter(self):
        exc = self._makeOne(body='123')
        self.assertEqual(exc.app_iter, ['123'])

    def test_ctor_with_unicode_body_doesnt_set_default_app_iter(self):
        exc = self._makeOne(unicode_body=u'123')
        self.assertEqual(exc.app_iter, ['123'])

    def test_ctor_with_app_iter_doesnt_set_default_app_iter(self):
        exc = self._makeOne(app_iter=['123'])
        self.assertEqual(exc.app_iter, ['123'])

    def test_ctor_with_body_sets_default_app_iter_html(self):
        cls = self._getTargetSubclass()
        exc = cls('detail')
        environ = _makeEnviron()
        environ['HTTP_ACCEPT'] = 'text/html'
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertTrue(body.startswith('<html'))
        self.assertTrue('200 OK' in body)
        self.assertTrue('explanation' in body)
        self.assertTrue('detail' in body)
        
    def test_ctor_with_body_sets_default_app_iter_text(self):
        cls = self._getTargetSubclass()
        exc = cls('detail')
        environ = _makeEnviron()
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertEqual(body, '200 OK\n\nexplanation\n\n\ndetail\n\n')

    def test__str__detail(self):
        exc = self._makeOne()
        exc.detail = 'abc'
        self.assertEqual(str(exc), 'abc')
        
    def test__str__explanation(self):
        exc = self._makeOne()
        exc.explanation = 'def'
        self.assertEqual(str(exc), 'def')

    def test_wsgi_response(self):
        exc = self._makeOne()
        self.assertTrue(exc is exc.wsgi_response)

    def test_exception(self):
        exc = self._makeOne()
        self.assertTrue(exc is exc.exception)

    def test__calls_start_response(self):
        cls = self._getTargetSubclass()
        exc = cls()
        environ = _makeEnviron()
        start_response = DummyStartResponse()
        exc(environ, start_response)
        self.assertTrue(start_response.headerlist)
        self.assertEqual(start_response.status, '200 OK')

    def test__default_app_iter_no_comment_plain(self):
        cls = self._getTargetSubclass()
        exc = cls()
        environ = _makeEnviron()
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertEqual(body, '200 OK\n\nexplanation\n\n\n\n\n')

    def test__default_app_iter_with_comment_plain(self):
        cls = self._getTargetSubclass()
        exc = cls(comment='comment')
        environ = _makeEnviron()
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertEqual(body, '200 OK\n\nexplanation\n\n\n\ncomment\n')
        
    def test__default_app_iter_no_comment_html(self):
        cls = self._getTargetSubclass()
        exc = cls()
        environ = _makeEnviron()
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertFalse('<!-- ' in body)

    def test__default_app_iter_with_comment_html(self):
        cls = self._getTargetSubclass()
        exc = cls(comment='comment & comment')
        environ = _makeEnviron()
        environ['HTTP_ACCEPT'] = '*/*'
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertTrue('<!-- comment &amp; comment -->' in body)

    def test__default_app_iter_with_comment_html2(self):
        cls = self._getTargetSubclass()
        exc = cls(comment='comment & comment')
        environ = _makeEnviron()
        environ['HTTP_ACCEPT'] = 'text/html'
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertTrue('<!-- comment &amp; comment -->' in body)

    def test_custom_body_template(self):
        cls = self._getTargetSubclass()
        exc = cls(body_template='${REQUEST_METHOD}')
        environ = _makeEnviron()
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertEqual(body, '200 OK\n\nGET')

    def test_body_template_unicode(self):
        cls = self._getTargetSubclass()
        la = unicode('/La Pe\xc3\xb1a', 'utf-8')
        environ = _makeEnviron(unicodeval=la)
        exc = cls(body_template='${unicodeval}')
        start_response = DummyStartResponse()
        body = list(exc(environ, start_response))[0]
        self.assertEqual(body, '200 OK\n\n/La Pe\xc3\xb1a')

class TestRenderAllExceptionsWithoutArguments(unittest.TestCase):
    def _doit(self, content_type):
        from pyramid.httpexceptions import status_map
        L = []
        self.assertTrue(status_map)
        for v in status_map.values():
            environ = _makeEnviron()
            start_response = DummyStartResponse()
            exc = v()
            exc.content_type = content_type
            result = list(exc(environ, start_response))[0]
            if exc.empty_body:
                self.assertEqual(result, '')
            else:
                self.assertTrue(exc.status in result)
            L.append(result)
        self.assertEqual(len(L), len(status_map))
            
    def test_it_plain(self):
        self._doit('text/plain')

    def test_it_html(self):
        self._doit('text/html')

class Test_HTTPMove(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from pyramid.httpexceptions import _HTTPMove
        return _HTTPMove(*arg, **kw)

    def test_it_location_not_passed(self):
        exc = self._makeOne()
        self.assertEqual(exc.location, '')

    def test_it_location_passed(self):
        exc = self._makeOne(location='foo')
        self.assertEqual(exc.location, 'foo')

class TestHTTPForbidden(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from pyramid.httpexceptions import HTTPForbidden
        return HTTPForbidden(*arg, **kw)

    def test_it_result_not_passed(self):
        exc = self._makeOne()
        self.assertEqual(exc.result, None)

    def test_it_result_passed(self):
        exc = self._makeOne(result='foo')
        self.assertEqual(exc.result, 'foo')
        
class DummyRequest(object):
    exception = None

class DummyStartResponse(object):
    def __call__(self, status, headerlist):
        self.status = status
        self.headerlist = headerlist
        
def _makeEnviron(**kw):
    environ = {'REQUEST_METHOD':'GET',
               'wsgi.url_scheme':'http',
               'SERVER_NAME':'localhost',
               'SERVER_PORT':'80'}
    environ.update(kw)
    return environ
