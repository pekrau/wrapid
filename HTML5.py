""" wrapid: Web Resource API server framework built on Python WSGI.

HTML5 generation classes; minimalist version derived from HyperText/HTML40.py

See http://www.w3.org/TR/html5/
"""

__version__ = '12.5'

DOCTYPE = '<!DOCTYPE html>'

ENCODING = 'utf-8'

global_attrs = dict(accesskey=1,
                    klass=1,
                    contenteditable=1,
                    contextmenu=1,
                    dir=1,
                    draggable=1,
                    dropzone=1,
                    hidden=1,
                    id=1,
                    lang=1,
                    spellcheck=1,
                    style=1,
                    tabindex=1,
                    title=1,
                    translate=1)

event_attrs = dict(onabort=1,
                   onblur=1,
                   oncanplay=1,
                   oncanplaythrough=1,
                   onchange=1,
                   onclick=1,
                   oncontextmenu=1,
                   oncuechange=1,
                   ondblclick=1,
                   ondrag=1,
                   ondragend=1,
                   ondragenter=1,
                   ondragleave=1,
                   ondragover=1,
                   ondragstart=1,
                   ondrop=1,
                   ondurationchange=1,
                   onemptied=1,
                   onended=1,
                   onerror=1,
                   onfocus=1,
                   oninput=1,
                   oninvalid=1,
                   onkeydown=1,
                   onkeypress=1,
                   onkeyup=1,
                   onload=1,
                   onloadeddata=1,
                   onloadedmetadata=1,
                   onloadstart=1,
                   onmousedown=1,
                   onmousemove=1,
                   onmouseout=1,
                   onmouseover=1,
                   onmouseup=1,
                   onmousewheel=1,
                   onpause=1,
                   onplay=1,
                   onplaying=1,
                   onprogress=1,
                   onratechange=1,
                   onreset=1,
                   onscroll=1,
                   onseeked=1,
                   onseeking=1,
                   onselect=1,
                   onshow=1,
                   onstalled=1,
                   onsubmit=1,
                   onsuspend=1,
                   ontimeupdate=1,
                   onvolumechange=1,
                   onwaiting=1)

media_attrs = dict(src=1,
                   preload=1,
                   autoplay=0,
                   mediagroup=1,
                   loop=0,
                   muted=0,
                   controls=0)
dimension_attrs = dict(width=1, height=1)
anchor_attrs = dict(href=1,
                    rel=1,
                    media=1,
                    hreflang=1,
                    type=1)
input_basic_attrs = dict(autofocus=0,
                         disabled=0,
                         form=1,
                         name=1)
input_form_attrs = dict(formaction=1,
                        formenctype=1,
                        formmethod=1,
                        formnovalidate=0,
                        formtarget=1)


class Element(object):
    "Base HTML element."

    allow_content = True
    attrlist = global_attrs.copy()
    attrlist.update(event_attrs)
    defaults = dict()
    attr_translations = dict(klass='class',
                             html_class='class',
                             html_for='for',
                             http_equiv='http-equiv',
                             accept_charset='accept-charset')

    def __init__(self, *content, **attr):
	self.dict = dict()
        try:
            self.name = unicode(self.name)
        except AttributeError:
            self.name = unicode(self.__class__.__name__)
	self.update(self.defaults)
	self.update(attr)
	if not self.allow_content and content:
	    raise TypeError("no content for element '%s'" % self.name)
	self.content = list(content)

    def __len__(self):
        if self.allow_content:
            return len(self.content)
        else:
            return True

    def __getitem__(self, k):
        return self.dict[k]

    def __setitem__(self, k, v):
	kl = k.lower()
	if self.attrlist.has_key(kl):
            self.dict[kl] = v
	else:
            raise KeyError("invalid attribute '%s' for element '%s'" %
                           (k, self.name))

    def __str__(self, indent=0, perlevel=2):
        uvalue = self.__unicode__(indent=indent, perlevel=perlevel)
        return uvalue.encode(ENCODING)

    def __unicode__(self, indent=0, perlevel=2):
        if indent:
            result = [(perlevel and u'\n' or u'') + u' '*indent]
        else:
            result = [u'']
        attrs = []
        for key in self.dict:
            if self.attrlist.get(key, True):
                name = self.attr_translations.get(key, key)
                attrs.append(u'%s="%s"' % (name, self[key]))
            else:
                attrs.append(self[key] and key or u'')
        if attrs:
            result.append(u"<%s %s>" % (self.name, u' '.join(attrs)))
        else:
            result.append(u"<%s>" % (self.name))
	for c in self.content:
	    try:
                result.append(c.__unicode__(indent+perlevel, perlevel))
	    except:
                if isinstance(c, str):
                    result.append(unicode(c, ENCODING))
                elif isinstance(c, unicode):
                    result.append(c)
                else:
                    result.append(unicode(c))
        if self.allow_content:
            result.append(u"</%s>" % self.name)
	return u''.join(result)

    def update(self, d): 
	for k, v in d.iteritems():
            self[k] = v

    def append(self, *items):
        if self.allow_content:
            map(self.content.append, items)
        else:
	    raise TypeError('No content for this element')


class HTML(Element):
    attrlist = dict(manifest=1)
    attrlist.update(Element.attrlist)
    def __str__(self, indent=0, perlevel=2):
        return DOCTYPE + '\n' + super(HTML, self).__str__(indent=indent,
                                                          perlevel=perlevel)

class HEAD(Element): pass

class TITLE(Element): pass

class BASE(Element):
    allow_content = False
    attrlist = dict(href=1, target=1)
    attrlist.update(Element.attrlist)

class LINK(Element):
    allow_content = False
    attrlist = dict(sizes=1)
    attrlist.update(anchor_attrs)
    attrlist.update(Element.attrlist)

class META(Element):
    allow_content = False
    attrlist = dict(name=1, http_equiv=1, content=1, charset=1)
    attrlist.update(Element.attrlist)

class STYLE(Element):
    attrlist = dict(media=1, type=1, scoped=1)
    attrlist.update(Element.attrlist)

class SCRIPT(Element):
    attrlist = dict(src=1, async=1, defer=0, type=1, charset=1)
    attrlist.update(Element.attrlist)

class NOSCRIPT(Element): pass

class BODY(Element):
    attrlist = dict(onafterprint=1,
                    onbeforeprint=1,
                    onbeforeunload=1,
                    onblur=1,
                    onerror=1,
                    onfocus=1,
                    onhashchange=1,
                    onload=1,
                    onmessage=1,
                    onoffline=1,
                    ononline=1,
                    onpagehide=1,
                    onpageshow=1,
                    onpopstate=1,
                    onresize=1,
                    onscroll=1,
                    onstorage=1,
                    onunload=1)
    attrlist.update(Element.attrlist)

class SECTION(Element): pass
class NAV(Element): pass
class ARTICLE(Element): pass
class ASIDE(Element): pass

class H1(Element): pass
class H2(Element): pass
class H3(Element): pass
class H4(Element): pass
class H5(Element): pass
class H6(Element): pass
class HGROUP(Element): pass
class HEADER(Element): pass
class FOOTER(Element): pass
class ADDRESS(Element): pass
class P(Element): pass

class HR(Element):
    allow_content = False

class PRE(Element): pass

class BLOCKQUOTE(Element):
    attrlist = dict(cite=1)
    attrlist.update(Element.attrlist)

class OL(Element):
    attrlist = dict(reversed=1, start=1, type=1)
    attrlist.update(Element.attrlist)

class UL(Element): pass

class LI(Element):
    attrlist = dict(value=1)
    attrlist.update(Element.attrlist)

class DL(Element): pass
class DT(Element): pass
class DD(Element): pass
class FIGURE(Element): pass
class FIGCAPTION(Element): pass
class DIV(Element): pass

class A(Element):
    attrlist = dict(target=1)
    attrlist.update(anchor_attrs)
    attrlist.update(Element.attrlist)
    
class EM(Element): pass
class STRONG(Element): pass
class SMALL(Element): pass
class S(Element): pass
class CITE(Element): pass
class Q(Element): pass
class DFN(Element): pass
class ABBR(Element): pass

class TIME(Element):
    attrlist = dict(datetime=1)
    attrlist.update(Element.attrlist)

class CODE(Element): pass
class VAR(Element): pass
class SAMP(Element): pass
class KBD(Element): pass
class SUB(Element): pass
class SUP(Element): pass
class I(Element): pass
class B(Element): pass
class U(Element): pass
class MARK(Element): pass
class RUBY(Element): pass
class RT(Element): pass
class RP(Element): pass
class BDI(Element): pass
class BDO(Element): pass
class SPAN(Element): pass

class BR(Element):
    allow_content = False

class WBR(Element):
    allow_content = False

class INS(Element):
    attrlist = dict(cite=1, datetime=1)
    attrlist.update(Element.attrlist)

class DEL(Element):
    attrlist = dict(cite=1, datetime=1)
    attrlist.update(Element.attrlist)

class IMG(Element):
    attrlist = dict(alt=1, src=1, crossorigin=1, usemap=1, ismap=0)
    attrlist.update(dimension_attrs)
    attrlist.update(Element.attrlist)

class IFRAME(Element):
    attrlist = dict(src=1, srcdoc=1, name=1, sandbox=1, seamless=0)
    attrlist.update(dimension_attrs)
    attrlist.update(Element.attrlist)

class EMBED(Element):
    attrlist = dict(src=1, type=1)
    attrlist.update(dimension_attrs)
    attrlist.update(Element.attrlist)

class OBJECT(Element):
    attrlist = dict(data=1, type=1, typemustmatch=0, name=1, usemap=1, form=1)
    attrlist.update(dimension_attrs)
    attrlist.update(Element.attrlist)

class PARAM(Element):
    allow_content = False
    attrlist = dict(name=1, value=1)
    attrlist.update(Element.attrlist)

class VIDEO(Element):
    attrlist = dict(crossorigin=1, poster=1)
    attrlist.update(dimension_attrs)
    attrlist.update(media_attrs)
    attrlist.update(Element.attrlist)

class AUDIO(Element):
    attrlist = dict(crossorigin=1)
    attrlist.update(media_attrs)
    attrlist.update(Element.attrlist)

class SOURCE(Element):
    attrlist = dict(src=1, type=1, media=1)
    attrlist.update(Element.attrlist)

class TRACK(Element):
    attrlist = dict(kind=1, src=1, srclang=1, label=1, default=1)
    attrlist.update(Element.attrlist)

class CANVAS(Element):
    attrlist = dimension_attrs.copy()
    attrlist.update(Element.attrlist)

class MAP(Element):
    attrlist = dict(name=1)
    attrlist.update(Element.attrlist)

class AREA(Element):
    attrlist = dict(alt=1, coords=1, shape=1, target=1)
    attrlist.update(anchor_attrs)
    attrlist.update(Element.attrlist)

class TABLE(Element):
    attrlist = dict(border=1)
    attrlist.update(Element.attrlist)

class CAPTION(Element): pass

class COLGROUP(Element):
    attrlist = dict(span=1)
    attrlist.update(Element.attrlist)

class COL(Element):
    attrlist = dict(span=1)
    attrlist.update(Element.attrlist)

class TBODY(Element): pass
class THEAD(Element): pass
class TFOOT(Element): pass
class TR(Element): pass

class TD(Element):
    attrlist = dict(colspan=1, rowspan=1, headers=1)
    attrlist.update(Element.attrlist)

class TH(Element):
    attrlist = dict(colspan=1, rowspan=1, headers=1, scope=1)
    attrlist.update(Element.attrlist)

class FORM(Element):
    attrlist = dict(accept_charset=1,
                    action=1,
                    autocomplete=1,
                    enctype=1,
                    method=1,
                    name=1,
                    novalidate=0,
                    target=1)
    attrlist.update(Element.attrlist)

class FIELDSET(Element):
    attrlist = dict(disabled=0, form=1, name=1)
    attrlist.update(Element.attrlist)

class LEGEND(Element): pass

class LABEL(Element):
    attrlist = dict(form=1, html_for=1)
    attrlist.update(Element.attrlist)

class INPUT(Element):
    allow_content = False
    attrlist = dict(accept=1, 
                    alt=1,
                    autocomplete=1,
                    checked=0,
                    dirname=1,
                    list=1,
                    max=1,
                    maxlength=1,
                    min=1,
                    multiple=0,
                    pattern=1,
                    placeholder=1,
                    readonly=0,
                    required=0,
                    size=1,
                    src=1,
                    step=1,
                    type=1,
                    value=1)
    attrlist.update(input_basic_attrs)
    attrlist.update(input_form_attrs)
    attrlist.update(dimension_attrs)
    attrlist.update(Element.attrlist)

class BUTTON(Element):
    attrlist = dict(type=1, value=1)
    attrlist.update(input_basic_attrs)
    attrlist.update(input_form_attrs)
    attrlist.update(Element.attrlist)

class SELECT(Element):
    attrlist = dict(multiple=0, required=0, size=1)
    attrlist.update(input_basic_attrs)
    attrlist.update(Element.attrlist)

class DATALIST(Element): pass

class OPTGROUP(Element):
    attrlist = dict(disabled=0, label=1)
    attrlist.update(Element.attrlist)

class OPTION(Element):
    attrlist = dict(disabled=0, label=1, selected=0, value=1)
    attrlist.update(Element.attrlist)

class TEXTAREA(Element):
    attrlist = dict(cols=1, dirname=1, maxlength=1, placeholder=1,
                    readonly=0, required=0, rows=1, wrap=1)
    attrlist.update(input_basic_attrs)
    attrlist.update(Element.attrlist)

class KEYGEN(Element):
    attrlist = dict(challenge=1, keytype=1)
    attrlist.update(input_basic_attrs)
    attrlist.update(Element.attrlist)

class OUTPUT(Element):
    attrlist = dict(html_for=1, form=1, name=1)
    attrlist.update(Element.attrlist)

class PROGRESS(Element):
    attrlist = dict(value=1, max=1)
    attrlist.update(Element.attrlist)

class METER(Element):
    attrlist = dict(value=1, min=1, max=1, low=1, hight=1, optimum=1)
    attrlist.update(Element.attrlist)

class DETAILS(Element):
    attrlist = dict(open=0)
    attrlist.update(Element.attrlist)

class SUMMARY(Element): pass

class COMMAND(Element):
    attrlist = dict(type=1,
                    label=1,
                    icon=1,
                    disabled=0,
                    checked=0,
                    radiogroup=1,
                    command=1)
    attrlist.update(Element.attrlist)

class MENU(Element):
    attrlist = dict(type=1, label=1)
    attrlist.update(Element.attrlist)


if __name__ == '__main__':
    import codecs
    swedish = codecs.open('swedish.txt', 'r', 'utf-8').read()
    title = swedish.split('\n')[0]
    print HTML(HEAD(META(charset=ENCODING),
                    TITLE(title)),
               BODY(H1(title, klass='stuff'),
                    P(swedish, onfocus='doit()'),
                    P(A('Link to SciLifeLab',
                        href='http://www.scilifelab.se/')),
                    FORM(INPUT(type='submit', disabled=True),
                         action='doit.html'),
                    TABLE(TR(TH('Header')),
                          TR(TD('Cell')),
                          klass="main")),
               lang='sv')
