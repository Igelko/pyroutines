#! /usr/bin/python
# coding: utf-8
# pragma: shitcode

import re
import os
import sys
from fnmatch import fnmatch
import email
from email.header import decode_header
import errno
import mimetypes
import argparse
import encodings


codecs = sorted(encodings.aliases.aliases.values())

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputdir", "-od", metavar="outputdir", help="output directory", required=True)

    subparsers = parser.add_subparsers(help="file or directory")
    f_parser = subparsers.add_parser("f", help="single file to process")
    f_parser.add_argument("filename", type=str, help="single file to process",)
    d_parser = subparsers.add_parser("d", help="process files in directory")
    d_parser.add_argument("directory", type=str, help="process files in directory")
    d_parser.add_argument("--mask", "-m", default="*", metavar="mask", help="mask to filter input files")

    a = parser.parse_args()
    return a


def force_decode(string, codecs=codecs):
    for i in codecs:
        try:
            return string.decode(i)
        except:
            pass
    else:
        raise Exception("Unknown codec!")


def unpack(input_dir, input_file, outputdir):
    with open(os.path.join(input_dir, input_file), "rb") as fp:
        msg = email.message_from_file(fp)
    counter =0
    for part in msg.walk():
        # multipart/* are just containers
        try:
            if part.get_content_maintype() == 'multipart':
                continue
            # Applications should really sanitize the given filename so that an
            # email message can't be used to overwrite important files
            m_filename = part.get_filename()
            filename = m_filename
            if filename:
                if filename.startswith("=?"):
                    decoded = decode_header(filename)
                    filename = decoded[0][0].decode(decoded[0][1].upper())
                else:
                    if isinstance(filename, str):
                        filename = force_decode(filename)
                filename = input_file.decode("utf-8") + "_" + filename
            else:
                ext = mimetypes.guess_extension(part.get_content_type())
                if not ext:
                # Use a generic bag-of-bits extension
                    ext = '.bin'
                filename =u'%s_part-%03d%s' % (input_file, counter, ext)

            filename = filename.encode("utf-8")
            with open(os.path.join(outputdir, filename), 'wb') as of:
                of.write(part.get_payload(decode=True))
            counter += 1
        except UnicodeDecodeError as e:
            print "oops:"
            print input_file
            print "encoded: ", type(m_filename), m_filename.encode("string_escape")
            if m_filename and m_filename.startswith("=?"):
                decoded = decode_header(m_filename)
                print "tuple: ", type(decoded), decoded

def main():
    args = parse_arguments()
    print args
    if "directory" in args:

        for fname in os.listdir(args.directory):
            if fnmatch(fname, args.mask):
                unpack(args.directory, fname, args.outputdir)
    elif args.filename:
        fdir, fname = os.path.split(args.filename)
        unpack(fdir, fname, args.outputdir)

if __name__ == "__main__":
    main()

