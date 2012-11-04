#!/usr/bin/python
# -*- coding: utf-8 -*-

## id3tagextractor.py version 1.0 - Last modified 2 April 2009
## Copyright 2009 Michael Johnson
## See www.chippedprism.com for more information (including
## contact information)

## This program depends on the external Python module Mutagen,
## which is used as the audio tagging backend for Quod Libet and
## Ex Falso, among others.Currently it may be obtained from
## the Quod Libet Google Code page:
## http://code.google.com/p/quodlibet/wiki/Mutagen

## This script is believed to work with Python 2.5 and 2.6 on Linux
## and Windows, with Mutagen 1.16.


from mutagen.id3 import ID3,ID3NoHeaderError
from StringIO import StringIO
from xml.sax.saxutils import escape
from optparse import OptionParser
import os
import sys


## Define functions

def opt_parser():
    """Creates a parser (using OptionParser) to handle arguments."""

    usage = """usage: %prog [options] DIR
    Creates an XML file containing the ID3 tag data from all the files
    with a specified extension in DIR."""
    parser = OptionParser(usage=usage, version="%prog 1.0")
    parser.add_option("-e", "--extension",
                      action="store", type="string", dest="ext", default="mp3",
                      help="extension to search for [default: %default]")
    parser.add_option("-r", action="store_true", dest="recurse", default=False,
                      help="recursively scan all subdirectories")
    (options,args) = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments. Specify a target directory "
                     "and output file name.")
    return parsed_variables(options,args)

def parsed_variables(options,args):
    """Takes arguments and options from the parser and returns several variables."""
    base_dir = os.path.abspath(args[0])
    outputfile = os.path.abspath(args[1])
    os.chdir(base_dir)
    tree = os.walk(base_dir)
    target_ext = options.ext.strip('.').lower()
    recurse = options.recurse
    return tree,target_ext,recurse,outputfile

def create_tag_string(tags):
    """Takes a tag list and returns an XML string defining all tags."""
    tag_stringfile = StringIO()
    tag_stringfile.write(u'\t\t<tags>\n')
    for x in range(0,len(tags)):
        tagname = escape(tags[x][0])
        tagvalue = escape(tags[x][1])
        tagstring = ''.join((u'\t\t\t<',tagname,u'>',tagvalue,u'</',tagname,u'>\n'))
        tag_stringfile.write(tagstring)
    tag_stringfile.write(u'\t\t</tags>\n')
    return tag_stringfile.getvalue()

def create_song_string(filename,currdir):
    """Takes a file name and the current directory and returns an XML string for a song."""
    song_stringfile = StringIO()
    song_stringfile.write(u'\t<song>\n')
    currdir = currdir.decode(sys.getfilesystemencoding()) # Handles non-ASCII characters in file/directory names
    filename = filename.decode(sys.getfilesystemencoding()) 
    location = escape(os.path.join(currdir,filename))
    location = ''.join((u'\t\t<location>',location,u'</location>\n'))
    song_stringfile.write(location)

    mediafilename = os.path.join(currdir,filename)
    mediafile = open_media(mediafilename)

    if mediafile:
        metadata = mediafile.pprint() # gets all metadata
        tags = [x.split('=',1) for x in metadata[0:].split('\n')]
        for x in range(tags.count([u''])): # removes blank lines (which cause errors later)
            tags.remove([u''])
        song_stringfile.write(create_tag_string(tags)) # Write all tags
    else:
        song_stringfile.write(u'\t\t<tags>\n\t\t</tags>\n')
        
    song_stringfile.write('\t</song>\n')
    return song_stringfile.getvalue()

def open_media(mediafilename):
    """Takes the name of a media file and attempts to open it with Mutagen."""
    try:
        mediafile = ID3(mediafilename)
    except ID3NoHeaderError:
        return None
    else:
        mediafile.update_to_v24() # in case we want to write these values later
                                  # (mutagen can only write ID3v2.4 tags to files)
        return mediafile
    
def save_output(outputfile,stringfile):
    """Saves the contents of a StringIO object to an output file."""
    outfile = open(outputfile,'w')
    outfile.write(stringfile.getvalue().encode("utf-8"))
    outfile.close()
    return None


## Main

(tree,target_ext,recurse,outputfile) = opt_parser()
stringfile = StringIO() # fast concatenation while building output file
stringfile.write(u'<?xml encoding="UTF-8"?>\n<tags_extracted>\n')

# Start walking the tree
for branch in tree:
    filelist = branch[2]
    currdir = branch[0]
    for filename in filelist:
        file_ext = os.path.splitext(filename)[1].lower().strip('.')
        if  file_ext == target_ext:
            stringfile.write(create_song_string(filename,currdir))
    if recurse == False:
        break

stringfile.write(u'</tags_extracted>')

# Save output
save_output(outputfile,stringfile)

stringfile.close()
