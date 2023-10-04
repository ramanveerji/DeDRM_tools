#! /usr/bin/python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import csv
import os
import getopt
from struct import pack
from struct import unpack


class PParser(object):
    def __init__(self, gd, flatxml, meta_array):
        self.gd = gd
        self.flatdoc = flatxml.split(b'\n')
        self.docSize = len(self.flatdoc)
        self.temp = []

        self.ph = -1
        self.pw = -1
        startpos = self.posinDoc('page.h') or self.posinDoc('book.h')
        for p in startpos:
            (name, argres) = self.lineinDoc(p)
            self.ph = max(self.ph, int(argres))
        startpos = self.posinDoc('page.w') or self.posinDoc('book.w')
        for p in startpos:
            (name, argres) = self.lineinDoc(p)
            self.pw = max(self.pw, int(argres))

        if self.ph <= 0:
            self.ph = int(meta_array.get('pageHeight', '11000'))
        if self.pw <= 0:
            self.pw = int(meta_array.get('pageWidth', '8500'))

        res = []
        startpos = self.posinDoc('info.glyph.x')
        for p in startpos:
            argres = self.getDataatPos('info.glyph.x', p)
            res.extend(argres)
        self.gx = res

        res = []
        startpos = self.posinDoc('info.glyph.y')
        for p in startpos:
            argres = self.getDataatPos('info.glyph.y', p)
            res.extend(argres)
        self.gy = res

        res = []
        startpos = self.posinDoc('info.glyph.glyphID')
        for p in startpos:
            argres = self.getDataatPos('info.glyph.glyphID', p)
            res.extend(argres)
        self.gid = res


    # return tag at line pos in document
    def lineinDoc(self, pos) :
        if (pos >= 0) and (pos < self.docSize) :
            item = self.flatdoc[pos]
            if item.find(b'=') >= 0:
                (name, argres) = item.split(b'=',1)
            else :
                name = item
                argres = b''
        return name, argres

    # find tag in doc if within pos to end inclusive
    def findinDoc(self, tagpath, pos, end):
        result = None
        end = self.docSize if end == -1 else min(self.docSize, end)
        foundat = -1
        for j in range(pos, end):
            item = self.flatdoc[j]
            if item.find(b'=') >= 0:
                (name, argres) = item.split(b'=',1)
            else :
                name = item
                argres = b''
            if (isinstance(tagpath,str)):
                tagpath = tagpath.encode('utf-8')
            if name.endswith(tagpath) :
                result = argres
                foundat = j
                break
        return foundat, result

    # return list of start positions for the tagpath
    def posinDoc(self, tagpath):
        startpos = []
        pos = 0
        res = ""
        while res != None :
            (foundpos, res) = self.findinDoc(tagpath, pos, -1)
            if res != None :
                startpos.append(foundpos)
            pos = foundpos + 1
        return startpos

    def getData(self, path):
        result = None
        cnt = len(self.flatdoc)
        for j in range(cnt):
            item = self.flatdoc[j]
            if item.find(b'=') >= 0:
                (name, argt) = item.split(b'=')
                argres = argt.split(b'|')
            else:
                name = item
                argres = []
            if (name.endswith(path)):
                result = argres
                break
        if (len(argres) > 0) :
            for j in range(0,len(argres)):
                argres[j] = int(argres[j])
        return result

    def getDataatPos(self, path, pos):
        item = self.flatdoc[pos]
        if item.find(b'=') >= 0:
            (name, argt) = item.split(b'=')
            argres = argt.split(b'|')
        else:
            name = item
            argres = []
        if (len(argres) > 0) :
            for j in range(0,len(argres)):
                argres[j] = int(argres[j])
        if (isinstance(path,str)):
            path = path.encode('utf-8')
        return argres if (name.endswith(path)) else None

    def getDataTemp(self, path):
        result = None
        cnt = len(self.temp)
        for j in range(cnt):
            item = self.temp[j]
            if item.find(b'=') >= 0:
                (name, argt) = item.split(b'=')
                argres = argt.split(b'|')
            else:
                name = item
                argres = []
            if (isinstance(path,str)):
                path = path.encode('utf-8')
            if (name.endswith(path)):
                result = argres
                self.temp.pop(j)
                break
        if (len(argres) > 0) :
            for j in range(0,len(argres)):
                argres[j] = int(argres[j])
        return result

    def getImages(self):
        result = []
        self.temp = self.flatdoc
        while (self.getDataTemp('img') != None):
            h = self.getDataTemp('img.h')[0]
            w = self.getDataTemp('img.w')[0]
            x = self.getDataTemp('img.x')[0]
            y = self.getDataTemp('img.y')[0]
            src = self.getDataTemp('img.src')[0]
            result.append('<image xlink:href="../img/img%04d.jpg" x="%d" y="%d" width="%d" height="%d" />\n' % (src, x, y, w, h))
        return result

    def getGlyphs(self):
        result = []
        if (self.gid != None) and (len(self.gid) > 0):
            glyphs = sorted(set(self.gid))
            for gid in glyphs:
                id='id="gl%d"' % gid
                if path := self.gd.lookup(id):
                    result.append(f'{id} {path}')
        return result


def convert2SVG(gdict, flat_xml, pageid, previd, nextid, svgDir, raw, meta_array, scaledpi):
    pp = PParser(gdict, flat_xml, meta_array)
    mlst = ['<?xml version="1.0" standalone="no"?>\n']
    if raw:
        mlst.extend(
            (
                '<!DOCTYPE svg PUBLIC "-//W3C/DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n',
                '<svg width="%fin" height="%fin" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">\n'
                % (pp.pw / scaledpi, pp.ph / scaledpi, pp.pw - 1, pp.ph - 1),
                '<title>Page %d - %s by %s</title>\n'
                % (pageid, meta_array['Title'], meta_array['Authors']),
            )
        )
    else:
        mlst.extend(
            (
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n',
                '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" ><head>\n',
                '<title>Page %d - %s by %s</title>\n'
                % (pageid, meta_array['Title'], meta_array['Authors']),
                '<script><![CDATA[\n',
                'function gd(){var p=window.location.href.replace(/^.*\?dpi=(\d+).*$/i,"$1");return p;}\n',
                'var dpi=%d;\n' % scaledpi,
            )
        )
        if (previd) :
            mlst.append('var prevpage="page%04d.xhtml";\n' % (previd))
        if (nextid) :
            mlst.append('var nextpage="page%04d.xhtml";\n' % (nextid))
        mlst.extend(
            (
                'var pw=%d;var ph=%d;' % (pp.pw, pp.ph),
                'function zoomin(){dpi=dpi*(0.8);setsize();}\n',
                'function zoomout(){dpi=dpi*1.25;setsize();}\n',
                'function setsize(){var svg=document.getElementById("svgimg");var prev=document.getElementById("prevsvg");var next=document.getElementById("nextsvg");var width=(pw/dpi)+"in";var height=(ph/dpi)+"in";svg.setAttribute("width",width);svg.setAttribute("height",height);prev.setAttribute("height",height);prev.setAttribute("width","50px");next.setAttribute("height",height);next.setAttribute("width","50px");}\n',
                'function ppage(){window.location.href=prevpage+"?dpi="+Math.round(dpi);}\n',
                'function npage(){window.location.href=nextpage+"?dpi="+Math.round(dpi);}\n',
                'var gt=gd();if(gt>0){dpi=gt;}\n',
                'window.onload=setsize;\n',
                ']]></script>\n',
                '</head>\n',
                '<body onLoad="setsize();" style="background-color:#777;text-align:center;">\n',
                '<div style="white-space:nowrap;">\n',
            )
        )
        if previd is None:
            mlst.append('<a href="javascript:ppage();"><svg id="prevsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"></svg></a>\n')
        else:
            mlst.append('<a href="javascript:ppage();"><svg id="prevsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"><polygon points="5,150,95,5,95,295" fill="#AAAAAA" /></svg></a>\n')

        mlst.append('<a href="javascript:npage();"><svg id="svgimg" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" style="background-color:#FFF;border:1px solid black;">' % (pp.pw, pp.ph))
    if (pp.gid != None):
        mlst.append('<defs>\n')
        gdefs = pp.getGlyphs()
        mlst.extend(gdefs[j] for j in range(0,len(gdefs)))
        mlst.append('</defs>\n')
    img = pp.getImages()
    if (img != None):
        mlst.extend(img[j] for j in range(0,len(img)))
    if (pp.gid != None):
        mlst.extend(
            '<use xlink:href="#gl%d" x="%d" y="%d" />\n'
            % (pp.gid[j], pp.gx[j], pp.gy[j])
            for j in range(0, len(pp.gid))
        )
    if (img is None or len(img) == 0) and (pp.gid is None or len(pp.gid) == 0):
        xpos = "%d" % (pp.pw // 3)
        ypos = "%d" % (pp.ph // 3)
        mlst.append(
            f'<text x="{xpos}" y="{ypos}" font-size="'
            + meta_array['fontSize']
            + '" font-family="Helvetica" stroke="black">This page intentionally left blank.</text>\n'
        )
    if raw:
        mlst.append('</svg>')
    else:
        mlst.append('</svg></a>\n')
        if nextid is None:
            mlst.append('<a href="javascript:npage();"><svg id="nextsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"></svg></a>\n')
        else:
            mlst.append('<a href="javascript:npage();"><svg id="nextsvg" viewBox="0 0 100 300" xmlns="http://www.w3.org/2000/svg" version="1.1" style="background-color:#777"><polygon points="5,5,5,295,95,150" fill="#AAAAAA" /></svg></a>\n')
        mlst.extend(
            (
                '</div>\n',
                '<div><a href="javascript:zoomin();">zoom in</a> - <a href="javascript:zoomout();">zoom out</a></div>\n',
                '</body>\n',
                '</html>\n',
            )
        )
    return "".join(mlst)
