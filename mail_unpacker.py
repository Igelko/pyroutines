#! /usr/bin/python
# coding: utf-8
# pragma: shitcode

import re
import os
import shutil
import sys
import email
import errno
import mimetypes
import argparse
import subprocess

from email.header import decode_header
from fnmatch import fnmatch

from tempdir import TempDir


fs_enc = sys.getfilesystemencoding()
target_exts = []
arch_exts = ['.rar', '.zip', '.qwe']


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputdir", "-od", metavar="outputdir", help="output directory", required=True)
    parser.add_argument("--7zip", "-7z", default="", help="path to 7z", dest='unpacker')
    parser.add_argument("--targets", '-t', help="target file types", default="ksh:xml:dbf")
    parser.add_argument("--exclude", '-x', help="excluded file mask", default="*e*.qwe")
    parser.add_argument("--remove", '-r', const=True, default=False, action='store_const', help="remove files after unpacking")
    parser.add_argument("--tempdir", "-td", metavar="tempdir", help="temporary directory", default=None)
    subparsers = parser.add_subparsers(help="file or directory")
    f_parser = subparsers.add_parser("f", help="single file to process")
    f_parser.add_argument("filename", type=str, help="single file to process",)
    d_parser = subparsers.add_parser("d", help="process files in directory")
    d_parser.add_argument("directory", type=str, help="process files in directory")
    d_parser.add_argument("--mask", "-m", default="*", metavar="mask", help="mask to filter input files")
    a = parser.parse_args()
    a.targets = map(lambda x: '.'+x, a.targets.lower().split(":"))
    return a


check_invalid = re.compile('[^\w\-_\. ]')

def escape_chars(s):
    return re.sub(check_invalid, '_', s)



def unpack_arch(input_file, output_dir, cfg):
    if not os.path.isfile(cfg.unpacker):
        raise Exception("Can't unpack archives without correct 7z executable!")
    try:
        command = "%(cmd)s e -bd -o%(dir)s %(file)s"
        args = {'cmd':cfg.unpacker, "file":input_file, "dir":output_dir}
        out = subprocess.check_output(command % args, shell=True)
        os.remove(input_file)
    except subprocess.CalledProcessError as e:
        print "Unpacker Error: ", e.output
    return os.listdir(output_dir)



def unpack_msg(input_file, output_dir, cfg):
    target_exts = cfg.targets
    with open(input_file, "rb") as fp:
        msg = email.message_from_file(fp)
    only_input_filename = os.path.split(input_file)[1]
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
                    filename = escape_chars(filename)
                filename = only_input_filename.decode("utf-8") + "_" + filename
                ext = os.path.splitext(filename)[1].lower()
            else:
                ext = mimetypes.guess_extension(part.get_content_type())
                if not ext:
                # Use a generic bag-of-bits extension
                    ext = '.bin'
                filename =u'%s_part-%03d%s' % (only_input_filename, counter, ext)
            filename = filename.encode(fs_enc)
            if ext in cfg.targets:
                with open(os.path.join(output_dir, filename), 'wb') as of:
                    of.write(part.get_payload(decode=True))
            elif ext in arch_exts and not fnmatch(filename, cfg.exclude):
                with TempDir(dir=cfg.tempdir) as temp:
                    archpath = os.path.join(temp, filename)
                    with open(archpath, 'wb') as of:
                        of.write(part.get_payload(decode=True))
                    for f in unpack_arch(archpath, temp, cfg):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in cfg.targets and not fnmatch(f, cfg.exclude):
                            path_from  = os.path.join(temp, f)
                            path_to = os.path.join(output_dir, filename+'_'+f)
                            shutil.copy(path_from, path_to)

            counter += 1
        except UnicodeDecodeError as e:
            print "oops:"
            print input_file
            raise
            print "encoded: ", type(m_filename), m_filename.encode("string_escape")
            if m_filename and m_filename.startswith("=?"):
                decoded = decode_header(m_filename)
                print "tuple: ", type(decoded), decoded
    if cfg.remove==True:
        os.remove(input_file)


def main():
    args = parse_arguments()
    if not os.path.isdir(args.outputdir):
        raise Exception("Output dir does not exists!")
    if "directory" in args:
        for fname in os.listdir(args.directory):
            if fnmatch(fname, args.mask):
                unpack_msg(os.path.join(args.directory, fname), args.outputdir, args)
    elif args.filename:
        unpack_msg(args.filename, args.outputdir, args)

if __name__ == "__main__":
    main()

