"""
This python library allows conversion of gds (gdsII/gds2) files / gdspy
libraries to latex (and subsequent svg, pdf, png, jpeg, ...).
More information on https://github.com/Aypac/GDSLatexConverter
@author René Vollmer
"""

import gdspy
import numpy as np
import re
#import hashlib
#import base64


class GDSLatexConverter:
    _latex = None
    _BIND = '--'
    _TAB = "    "
    __version__ = '0.11'

    def __init__(self, gdslibrary: gdspy.GdsLibrary):
        assert type(gdslibrary) is gdspy.GdsLibrary, 'Please pass a gdspy.GdsLibrary to the parameter gdslibrary.'
        self.gdslibrary = gdslibrary
        self.layer_per_cell = {}

        self.scale = 1
        self.layer_drawcolor = {}
        self.layer_drawopt = {}
        self.layer_per_cell = {}

        all_cells = self.gdslibrary.cell_dict
        self.all_layer = np.unique([k for l in all_cells.values()
                                    for k in l.get_layers()])

        self.layer_order = self.all_layer[:]

    def get_latex(self):
        if not self._latex:
            self.parse()
        return self._latex

    def _get_layer_options(self, layer):
        opt = ''
        if layer in self.layer_drawopt:
            opt = self.layer_drawopt[layer]
        color = 'black!20'
        if layer in self.layer_drawcolor:
            color = self.layer_drawcolor[layer]
        return 'draw=' + color + ', ' + opt

    def parse(self):
        fcts = ''
        pics = ''

        for cellname in self.gdslibrary.cell_dict:
            cell = self.gdslibrary.cell_dict[cellname]
            lpc = self._rec_check_poly(cell=cell)
            self.layer_per_cell[cellname] = lpc  # list(lpc[:])

        for cellname in self.gdslibrary.cell_dict:
            cell = self.gdslibrary.cell_dict[cellname]
            for layer in self.layer_order:
                pics += self._parse_cell(cell=cell, layer=layer)

        for layer in self.layer_order:
            for cell in self.gdslibrary.top_level():
                if layer in self.layer_per_cell[cell.name]:
                    opt = 'every path/.append style={' + self._get_layer_options(layer) + '}'
                    fcts += self._make_scope(cell=cell, layer=layer, options=opt)

        latex = """
% !TeX encoding = UTF-8
% !TeX spellcheck = en_GB

% Created with GDSLatexConverter v""" + self.__version__ + """
% For more information, visit https://github.com/Aypac/GDSLatexConverter 

\\documentclass[11pt,border=0mm]{standalone}
\\usepackage{mathptmx} %"Times New Roman" clone: Nimbus Roman No9 L

\\usepackage[utf8]{inputenc}

\\usepackage{tikz}
\\usetikzlibrary{patterns}
%\\usetikzlibrary{external} 
%\\tikzexternalize


% DEFINE PICS
"""
        latex += pics  # self._indent(tlc_pics)
        latex += "\n% END: DEFINE PICS\n\\begin{document}\n"
        latex += self._TAB + "\\begin{tikzpicture}\n"
        latex += self._indent(fcts, level=2) + "\n"
        latex += self._TAB + "\\end{tikzpicture}\n\\end{document}"
        self._latex = latex

    def _rec_check_poly(self, cell, layers=None):
        if layers is None:
            layers = np.array([])

        if hasattr(cell, 'polygons'):
            cl = cell.layers
            cl = [c for i, c in enumerate(cl)
                  if cell.polygons[i] is not None and len(cell.polygons[i]) > 0]
            layers = np.append(layers, cl)
            layers = np.unique(layers)

        if hasattr(cell, 'points'):
            layers = np.append(layers, [cell.layer])
            layers = np.unique(layers)

        if type(cell) is gdspy.Cell:
            for element in cell.elements:
                layers = self._rec_check_poly(cell=element, layers=layers)

        if hasattr(cell, 'ref_cell'):
            layers = self._rec_check_poly(cell=cell.ref_cell, layers=layers)

        return layers

    def _parse_cell(self, cell, layer):
        assert type(cell) is gdspy.Cell

        name = cell.name
        tex = ''
        polygons = ''
        scopes = ''
        for element in cell.elements:
            # ignore type(element) is gdspy.Cell
            if type(element) is gdspy.Cell:
                # if layer in self.layer_per_cell[name]:
                #    scopes += self._get_cell_call(cell=element, layer=layer) + '\n'
                _ = 0
            elif hasattr(element, 'ref_cell'):
                ref_cell = element.ref_cell  # this might be a string or object!
                ref_cell_name, ref_cell = self._cell(ref_cell)
                if layer in self.layer_per_cell[ref_cell_name]:
                    scopes += self._make_ref_scope(ref_cell=element,
                                                   layer=layer)
            elif hasattr(element, 'polygons'):
                polys = [p for i, p in enumerate(element.polygons)
                         if element.layers[i] == layer]
                if len(polys) > 0:
                    polygons += self._parse_polygons(points_list=polys,
                                                     layer=layer)
            elif hasattr(element, 'points'):
                if element.layer == layer:
                    polygons += self._parse_polygons(points_list=[element.points],
                                                     layer=layer)
            else:
                raise NotImplementedError('Not sure, what to do with this object:', element)

        if scopes != '' or polygons != '' or tex != '':
            tex += "% {}\n".format(name)
            tex += "\\tikzset {"
            tex += self._convert_name(cell=cell, layer=layer) + "/.pic={\n"
            inner = "% polygons in this cell\n"
            inner += polygons + "\n"
            inner += "% references in this cell to other cells\n"
            inner += scopes
            tex += self._indent(inner)
            tex += "\n}}\n"

        return tex

    def _parse_polygons(self, points_list, layer, addLayerOptions=False):
        """
        Turns a GDS polygon into a latex path.

        :param points_list:
        :param layer:
        :param addLayerOptions:
        :return: (str) latex path command
        """
        polygons_text = ''
        for i, points in enumerate(points_list):
            polygon_text = '\\path '
            if addLayerOptions:
                polygon_text += '[' + self._get_layer_options(layer) + ']'
            strs = ['({:.5f}, {:.5f})'.format(pts[0] * self.scale,
                                              pts[1] * self.scale)
                    for pts in points]
            polygon_text += self._BIND.join(strs)
            polygon_text += self._BIND + 'cycle {};\n'
            polygons_text += polygon_text
        return polygons_text

    def _make_scope(self, cell, layer, options):
        if type(options) is dict:
            options = ', '.join([str(k) + '=' + str(options[k]) for k in options])
        fct = self._get_cell_call(cell=cell, layer=layer)
        if options != '':
            scope = "\\begin{scope}[" + options + "]\n"
            scope += self._indent(fct)
            scope += "\n\\end{scope}\n"
            return scope
        else:
            return fct + "\n"

    def _make_ref_scope(self, ref_cell, layer, options=None):
        """
        This translates a GDS reference cell into a latex scope.
        It tries to produce as little code as possible.

        In GDS, the order of transformation is as follows:
            1. mirror
            2. rotation
            3. scale
            4. offset
        (Source: http://www.artwork.com/gdsii/gdsscale/index.htm )

        :param ref_cell:
        :param layer:
        :param options:
        :return:
        """

        needs_transform = False
        ref = type(ref_cell) is gdspy.CellReference
        refArr = type(ref_cell) is gdspy.CellArray
        assert ref or refArr, 'ref_cell is neither cell reference nor cell array'

        opt = options or {}

        magn = 1
        m = getattr(ref_cell, 'magnification', None)
        if m is not None and m != 0:
            magn = getattr(ref_cell, 'magnification')  # / self.scale
            needs_transform = True
        del m

        orig = getattr(ref_cell, 'origin', None)
        if orig is not None and (orig[0] != 0 or orig[1] != 0):
            o = getattr(ref_cell, 'origin')
            s = self.scale
            opt['shift'] = '{(%s, %s)}' % (o[0] * s, o[1] * s)

        xs = getattr(ref_cell, 'x_reflection', False)
        ys = getattr(ref_cell, 'y_reflection', False)
        xf = (1-2*xs)
        yf = (1-2*ys)
        if xs or ys:
            if magn != 1 or xs:
                opt['xscale'] = xf*magn
            if magn != 1 or ys:
                opt['yscale'] = yf*magn
            needs_transform = True
        elif magn != 1:
            opt['scale'] = magn
            needs_transform = True
        del xs, ys

        r = getattr(ref_cell, 'rotation', None)
        if r is not None and r != 0:
            opt['rotate'] = ((r + 180) % 360) - 180
            needs_transform = True
        del r

        if needs_transform:
            opt['every node/.append style'] = '{transform shape}'

        rows = getattr(ref_cell, 'rows', 1)
        cols = getattr(ref_cell, 'columns', 1)
        spacing = getattr(ref_cell, 'spacing', 0)

        rows, cols = 1, 1 #todo: remove
        if rows > 1 or cols > 1:
            # todo generalize for loop, using the spacing

            xtext = ''
            if rows > 1:
                xtext = '\\x'
            ytext = ''
            if cols > 1:
                ytext = '\\y'

            if 'shift' in opt:
                xtext += ' + '+str(opt['shift'][0])
                ytext += ' + '+str(opt['shift'][1])

            opt['shift'] = (xtext, ytext)

            scope = self._make_scope(cell=ref_cell.ref_cell, layer=layer,
                         options=opt)
            if rows > 1:
                scope = self._indent(scope)
                fl = '\\foreach \\x in {1,...,%d} {' % rows
                scope = fl + scope + '}'
            if cols > 1:
                scope = self._indent(scope)
                fl = '\\foreach \\y in {1,...,%d} {' % cols
                scope = fl + scope + '}'
            return scope
        else:
            return self._make_scope(cell=ref_cell.ref_cell, layer=layer,
                             options=opt)

    def _get_cell_call(self, cell, layer):
        return '\\pic{' + self._convert_name(cell=cell, layer=layer) + '};'

    def _convert_name(self, cell, layer: str = ''):
        name, cell = self._cell(cell)
        hash_txt = self._myhash(name)
        return self._conv_str(name) + '_' + self._conv_str(layer) + '_' + hash_txt

    def _myhash(self, str, length=5):
        # hasher = hashlib.sha1(string)
        # return base64.urlsafe_b64encode(hasher.digest()[0:10])
        p = 0
        for s in str:
            p += ord(s)
        c = '{:0%dX}' % length
        return c.format(p % (16 ** length))

    def _conv_str(self, string: str):
        string = str(string)
        sstr = re.sub('[\s]', '_', string)
        sstr = re.sub('[^\w_]', '', sstr)
        return sstr

    def _indent(self, text, level=1):
        text_arr = text.split("\n")
        t = self._TAB * level
        s = "\n" + t
        return t + s.join(text_arr)

    def _cell(self, cell):
        if type(cell) is str:
            name = cell
            cell = self.gdslibrary.cell_dict[name]
        else:
            name = cell.name
        return name, cell
