import gdspy
import numpy as np
import re
import hashlib
import base64


class GDSLatexConverter:
    _latex = None
    _BIND = ' -- '
    _TAB = "    "

    def __init__(self, gdslibrary: gdspy.GdsLibrary, layer_order: list = None):
        assert type(gdslibrary) is gdspy.GdsLibrary, 'Please pass a gdspy.GdsLibrary to the parameter gdslibrary.'
        self.gdslibrary = gdslibrary
        self.layer_per_cell = {}

        self.scale = 1e-2
        self.layer_drawcolor = {}
        self.layer_drawopt = {}
        self.layer_per_cell = {}

        all_cells = self.gdslibrary.cell_dict
        self.all_layer = np.unique([k for l in all_cells.values()
                                    for k in l.get_layers()])

        if layer_order is None:
            self.layer_order = self.all_layer[:]
        else:
            self.layer_order = layer_order

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
% !TeX spellcheck = de_DE

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

    def _get_elem_attr(self, element, attr: str, default=None):
        return getattr(element, attr, default)

    def _parse_polygons(self, points_list, layer):
        polygons_text = ''
        for i, points in enumerate(points_list):
            polygon_text = '\\path '  # ['+self._get_layer_options(layer)+']'
            points = np.append(points, [points[0]], axis=0)
            strs = ['({:.5f}, {:.5f})'.format(pts[0] * self.scale,
                                              pts[1] * self.scale)
                    for pts in points]
            polygon_text += self._BIND.join(strs)
            polygon_text += ' {};\n'
            polygons_text += polygon_text
        return polygons_text

    def _make_scope(self, cell, layer, options,
                    rows: int = 1, cols: int = 1, spacing: float = 0):
        if type(options) is dict:
            options = ', '.join([str(k) + '=' + str(options[k]) for k in options])
        fct = self._get_cell_call(cell=cell, layer=layer)
        scope = "\\begin{scope}[" + options + "]\n"
        scope += self._indent(fct)
        scope += "\n\\end{scope}\n"
        if rows > 1:
            # todo put in for loop
            scope = self._indent(scope)
            scope = '' + scope + ''
        if cols > 1:
            # todo put in for loop
            scope = self._indent(scope)
            scope = '' + scope + ''
        return scope

    def _make_ref_scope(self, ref_cell, layer, options=None):
        ref = type(ref_cell) is gdspy.CellReference
        refArr = type(ref_cell) is gdspy.CellArray
        assert ref or refArr, 'Is neither cell reference nor cell array'
        opt = options or {}
        if self._get_elem_attr(element=ref_cell, attr='origin') is not None:
            o = self._get_elem_attr(element=ref_cell, attr='origin')
            opt['shift'] = '{(%s, %s)}' % (o[0] * self.scale, o[1] * self.scale)
        if self._get_elem_attr(element=ref_cell, attr='magnification') is not None:
            opt['scale'] = self._get_elem_attr(element=ref_cell, attr='magnification')  # / self.scale
        if self._get_elem_attr(element=ref_cell, attr='rotation') is not None:
            opt['rotate'] = self._get_elem_attr(element=ref_cell, attr='rotation')
        if 'scale' in opt or 'rotate' in opt:
            opt['every node/.append style'] = '{transform shape}'

        r = self._get_elem_attr(element=ref_cell, attr='rows', default=1)
        c = self._get_elem_attr(element=ref_cell, attr='columns', default=1)
        s = self._get_elem_attr(element=ref_cell, attr='spacing', default=0)

        return self._make_scope(cell=ref_cell.ref_cell, layer=layer, options=opt,
                                rows=r, cols=c, spacing=s)

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
