#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division
import os

from PIL import Image
from optparse import OptionParser
from ox.image import drawText, wrapText

root_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
os.chdir(root_dir)


def render(infile, outfile):

    with open(infile) as f:

        image_size = (768, 1024)
        margin = 64
        offset = margin
        font_file = 'txt.ttf'
        font_size = 24
        line_height = 32
        max_lines = (image_size[1] - 2 * margin) / line_height

        image = Image.new('L', image_size, (255))

        for line in f:

            for line_ in line.strip().split('\r'):

                lines = wrapText(
                    line_,
                    image_size[0] - 2 * margin,
                    # we don't want the last line that ends with an ellipsis
                    max_lines + 1,
                    'txt.ttf',
                    font_size
                )

                for line__ in lines:
                    drawText(
                        image,
                        (margin, offset),
                        line__,
                        font_file,
                        font_size,
                        (0)
                    )
                    offset += line_height
                    max_lines -= 1

                    if max_lines == 0:
                        break

                if max_lines == 0:
                    break

            if max_lines == 0:
                break

        image.save(outfile)


def main():
    parser = OptionParser()
    parser.add_option(
        '-i', '--infile', dest='infile', help='txt file to be read'
    )
    parser.add_option(
        '-o', '--outfile', dest='outfile', help='jpg file to be written'
    )
    (options, args) = parser.parse_args()
    if None in (options.infile, options.outfile):
        parser.print_help()
    else:
        render(options.infile, options.outfile)


if __name__ == '__main__':
    main()

