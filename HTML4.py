""" wrapid: Web Resource API server framework built on Python WSGI.

HTML4 generation classes; minimalist version modified from HyperText/HTML40.py

See http://www.w3.org/TR/html4/
"""

__version__ = '12.5'

DOCTYPE = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"' \
          ' "http://www.w3.org/TR/html4/loose.dtd">'

ENCODING = 'utf-8'

core_attrs = dict(id=1, klass=1, style=1, title=1)
i18n = dict(lang=1, dir=1)
intrinsic_events = dict(onload=1, onunload=1, onclick=1,
                        ondblclick=1, onmousedown=1, onmouseup=1,
                        onmouseover=1, onmousemove=1, onmouseout=1,
                        onfocus=1, onblur=1, onkeypress=1,
                        onkeydown=1, onkeyup=1, onsubmit=1,
                        onreset=1, onselect=1, onchange=1)

common_attrs = core_attrs.copy()
common_attrs.update(i18n)
common_attrs.update(intrinsic_events)

alternate_text = dict(alt=1)
image_maps = dict(shape=1, coords=1)
anchor_reference = dict(href=1)
target_frame_info = dict(target=1)
tabbing_navigation = dict(tabindex=1)
access_keys = dict(accesskey=1)

tabbing_and_access = tabbing_navigation.copy()
tabbing_and_access.update(access_keys)

visual_presentation = dict(height=1, width=1, border=1, align=1,
                           hspace=1, vspace=1)

cellhalign = dict(align=1, char=1, charoff=1)
cellvalign = dict(valign=1)

font_modifiers = dict(size=1, color=1, face=1)

links_and_anchors = dict(href=1, hreflang=1, type=1, rel=1, rev=1)
borders_and_rules = dict(frame=1, rules=1, border=1)


class Element(object):
    "Base HTML element."

    allow_content = True
    defaults = dict()
    attrlist = dict()
    attr_translations = dict(klass='class',
                             html_class='class',
                             label_for='for',
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
	    raise TypeError('No content for this element')
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
            raise KeyError("Invalid attribute '%s' for element '%s'" %
                           (k, self.name))

    def __str__(self, indent=0, perlevel=2):
        uvalue = self.__unicode__(indent=indent, perlevel=perlevel)
        return uvalue.encode(ENCODING)

    def __unicode__(self, indent=0, perlevel=2):
        if indent:
            myindent = (perlevel and u'\n' or u'') + u' '*indent
        else:
            myindent = u''
	s = [myindent, self.start_tag()]
	for c in self.content:
	    try:
                s.append(c.__unicode__(indent+perlevel, perlevel))
	    except:
                if isinstance(c, str):
                    s.append(unicode(c, ENCODING))
                elif isinstance(c, unicode):
                    s.append(c)
                else:
                    s.append(unicode(c))
	s.append(self.end_tag())
	return u''.join(s)

    def start_tag(self):
        attrs = []
        for key in self.dict:
            if self.attrlist.get(key, True):
                attrs.append(u'%s="%s"' %
                             (self.attr_translations.get(key, key), self[key]))
            else:
                attrs.append(self[key] and key or u'')
        if attrs:
            return u"<%s %s>" % (self.name, u' '.join(attrs))
        else:
            return u"<%s>" % (self.name)

    def end_tag(self):
        if self.allow_content:
            return u"</%s>" % self.name
        else:
            return ''

    def update(self, d): 
	for k, v in d.iteritems():
            self[k] = v

    def append(self, *items):
        if self.allow_content:
            map(self.content.append, items)
        else:
	    raise TypeError('No content for this element')


class CommonElement(Element):
    attrlist = common_attrs

class A(CommonElement):
    attrlist = dict(name=1, charset=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(links_and_anchors)
    attrlist.update(image_maps)
    attrlist.update(target_frame_info)
    attrlist.update(tabbing_and_access)


class ABBR(CommonElement): pass
class ACRONYM(CommonElement): pass
class CITE(CommonElement): pass
class CODE(CommonElement): pass
class DFN(CommonElement): pass
class EM(CommonElement): pass
class KBD(CommonElement): pass
class PRE(CommonElement): pass
class SAMP(CommonElement): pass
class STRONG(CommonElement): pass
class VAR(CommonElement): pass
class ADDRESS(CommonElement): pass
class B(CommonElement): pass
class BIG(CommonElement): pass
class I(CommonElement): pass
class S(CommonElement): pass
class SMALL(CommonElement): pass
class STRIKE(CommonElement): pass
class TT(CommonElement): pass
class U(CommonElement): pass
class SUB(CommonElement): pass
class SUP(CommonElement): pass
 
class DD(CommonElement): pass
class DL(CommonElement): pass
class DT(CommonElement): pass
class NOFRAMES(CommonElement): pass
class NOSCRIPTS(CommonElement): pass
class P(CommonElement): pass

class AREA(CommonElement):
    attrlist = dict(name=1, nohref=0)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(image_maps)
    attrlist.update(anchor_reference)
    attrlist.update(tabbing_and_access)
    attrlist.update(alternate_text)

class MAP(AREA): pass

class BASE(Element):
    allow_content = False
    attrlist = anchor_reference.copy()
    attrlist.update(target_frame_info)

class BDO(Element):
    attrlist = core_attrs.copy()
    attrlist.update(i18n)

class BLOCKQUOTE(CommonElement):
    attrlist = dict(cite=1)
    attrlist.update(CommonElement.attrlist)

class Q(BLOCKQUOTE): pass

class BR(Element):
    allow_content = False
    attrlist = core_attrs

class BUTTON(CommonElement):
    attrlist = dict(name=1, value=1, type=1, disabled=0)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(tabbing_and_access)

class CAPTION(Element):
    attrlist = dict(align=1)
    attrlist.update(common_attrs)

class COLGROUP(CommonElement):
    attrlist = dict(span=1, width=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(cellhalign)
    attrlist.update(cellvalign)

class COL(COLGROUP):
    allow_content = False

class DEL(Element):
    attrlist = dict(cite=1, datetime=1)
    attrlist.update(common_attrs)

class INS(DEL): pass

class FIELDSET(CommonElement): pass

class LEGEND(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(access_keys)

class BASEFONT(Element):
    allow_content = False
    attrlist = dict(id=1)
    attrlist.update(font_modifiers)

class FONT(Element):
    attrlist = font_modifiers.copy()
    attrlist.update(core_attrs)
    attrlist.update(i18n)

class FORM(CommonElement):
    attrlist = dict(action=1, method=1, enctype=1, accept_charset=1, target=1)
    attrlist.update(CommonElement.attrlist)

class FRAME(Element):
    allow_content = False
    attrlist = dict(longdesc=1, name=1, src=1, frameborder=1,
                    marginwidth=1, marginheight=1, noresize=0, scrolling=1)
    attrlist.update(core_attrs)

class FRAMESET(Element):
    attrlist = dict(rows=1, cols=1, border=1)
    attrlist.update(core_attrs)
    attrlist.update(intrinsic_events)

class H1(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class H2(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class H3(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class H4(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class H5(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class H6(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class HEAD(Element):
    attrlist = dict(profile=1)
    attrlist.update(i18n)

class HR(Element):
    allow_content = False
    attrlist = dict(align=1, noshade=0, size=1, width=1)
    attrlist.update(core_attrs)
    attrlist.update(intrinsic_events)

class HTML(Element):
    attrlist = i18n

class TITLE(HTML): pass

class BODY(CommonElement):
    attrlist = dict(background=1, text=1, link=1, vlink=1, alink=1, bgcolor=1)
    attrlist.update(CommonElement.attrlist)

class IFRAME(Element):
    attrlist = dict(longdesc=1, name=1, src=1, frameborder=1,
                    marginwidth=1, marginheight=1, scrolling=1, 
                    align=1, height=1, width=1)
    attrlist.update(core_attrs)

class IMG(CommonElement):
    allow_content = False
    attrlist = dict(src=1, longdesc=1, usemap=1, ismap=0)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(visual_presentation)
    attrlist.update(alternate_text)

class INPUT(CommonElement):
    allow_content = False
    attrlist = dict(type=1, name=1, value=1, checked=0, disabled=0,
                    readonly=0, size=1, maxlength=1, src=1,
                    usemap=1, accept=1, border=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(tabbing_and_access)
    attrlist.update(alternate_text)

class LABEL(CommonElement):
    attrlist = dict(label_for=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(access_keys)

class UL(CommonElement):
    attrlist = dict(compact=0)
    attrlist.update(CommonElement.attrlist)

class OL(UL):
    attrlist = dict(start=1)
    attrlist.update(UL.attrlist)

class LI(UL):
    attrlist = dict(value=1, type=1)
    attrlist.update(UL.attrlist)

class LINK(CommonElement):
    allow_content = False
    attrlist = dict(charset=1, media=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(links_and_anchors)

class META(Element):
    allow_content = False
    attrlist = dict(http_equiv=1, name=1, content=1, scheme=1)
    attrlist.update(i18n)

class OBJECT(CommonElement):
    attrlist = dict(declare=0, classid=1, codebase=1, data=1,
                    type=1, codetype=1, archive=1, standby=1,
                    height=1, width=1, usemap=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(tabbing_navigation)

class SELECT(CommonElement):
    attrlist = dict(name=1, size=1, multiple=0, disabled=0)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(tabbing_navigation)

class OPTGROUP(CommonElement):
    attrlist = dict(disabled=0, label=1)
    attrlist.update(CommonElement.attrlist)

class OPTION(OPTGROUP):
    attrlist = dict(value=1, selected=0)
    attrlist.update(OPTGROUP.attrlist)

class PARAM(Element):
    attrlist = dict(id=1, name=1, value=1, valuetype=1, type=1)

class SCRIPT(Element):
    attrlist = dict(charset=1, type=1, src=1, defer=0)

class SPAN(CommonElement):
    attrlist = dict(align=1)
    attrlist.update(CommonElement.attrlist)

class DIV(SPAN): pass

class STYLE(Element):
    attrlist = dict(type=1, media=1, title=1)
    attrlist.update(i18n)

class TABLE(CommonElement):
    attrlist = dict(cellspacing=1, cellpadding=1, summary=1, align=1,
                    bgcolor=1, width=1)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(borders_and_rules)

class TBODY(CommonElement):
    attrlist = CommonElement.attrlist.copy()
    attrlist.update(cellhalign)
    attrlist.update(cellvalign)

class THEAD(TBODY): pass
class TFOOT(TBODY): pass
class TR(TBODY): pass

class TH(TBODY):
    attrlist = dict(abbv=1, axis=1, headers=1, scope=1,
                    rowspan=1, colspan=1, nowrap=0, width=1, height=1)
    attrlist.update(TBODY.attrlist)

class TD(TH): pass

class TEXTAREA(CommonElement):
    attrlist = dict(name=1, rows=1, cols=1, disabled=0, readonly=0)
    attrlist.update(CommonElement.attrlist)
    attrlist.update(tabbing_and_access)


if __name__ == '__main__':
    import codecs
    swedish = codecs.open('swedish.txt', 'r', 'utf-8').read()
    title = swedish.split('\n')[0]
    print DOCTYPE
    print HTML(HEAD(META(http_equiv='Content-Type',
                         content="text/html; charset=%s" % ENCODING),
                    TITLE(title)),
               BODY(H1(title, klass='stuff'),
                    P(swedish, onfocus='doit()'),
                    P(A('Link to SciLifeLab',
                        href='http://www.scilifelab.se/')),
                    FORM(INPUT(type='submit', disabled=True),
                         action='doit.html'),
                    TABLE(TR(TH('Header')),
                          TR(TD('Cell')),
                          border=1)))
