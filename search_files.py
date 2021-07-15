import os
import operator
from collections import Counter
from argparse import ArgumentParser
from files_n_dir import *

my_parser = ArgumentParser(prog='Search files',
                           usage='Search files in a given directory. May choose specific filetypes.',
                           description='Command Line Application searches a given directory and list and\
                               summarize then write on a text file.',
                           )
my_parser.add_argument('path', type=str, help='folder to be search of files')
my_parser.add_argument('-ext', '--file_extension', type=str,
                                                   default=None,
                                                   help='optional file extension that will be search')

args = my_parser.parse_args()

folder = args.path
file_ext = args.file_extension

# search all files and save its path and size to a text file and sort from largest to smallest
# then summarize the different filetypes

all_files = []
file_counter = Counter()
file_dic = {}

def remove_zfill(size):
    '''Remove all the zeros added that were help for sorting.'''
    if not size.startswith('0'):
        return size
    for char in size:
        if char == '0':
            return remove_zfill(size[1:])

def count_files(fext, size):
    '''Count files with the same extension, sum its size then store both 
    count and size in a list and store the list in a dictionary 
    with the key of file extension.'''
    if fext not in file_dic:
        file_dic[fext] = [1, size]
    else:
        file_dic[fext][0] += 1
        file_dic[fext][1] += size

def format_size(size):
    '''Format the different file sizes into B, KB, MB and GB.
    Returns the formatted size like '8.5 GB' and '5 MB'.'''
    size = remove_zfill(size)
    if len(size) <= 3:
        size = size + ' B'
        return size.rjust(9)
    elif len(size) <= 6:
        size = round(int(size)/1_000, 2)
        size = str(size) + ' KB'
        return size.rjust(9)
    elif len(size) <= 9:
        size = round(int(size)/1_000_000, 2)
        size = str(size) + ' MB'
        return size.rjust(9)
    else:
        size = round(int(size)/1_000_000_000, 2)
        size = str(size) + ' GB'
        return size.rjust(9)

def record_type_n_size(file):
    '''Record/Count the different file types. Calls count_files function'''
    size = os.path.getsize(file)
    _, fext = os.path.splitext(file)
    count_files(fext, size)

def match(file, ext):
    '''Check for optional file extension to search.
    Returns boolean'''
    return os.path.splitext(file)[1][1:] == ext


with open('outputs//map_files.txt', 'w', encoding='utf8') as text_file:
    for paths, dirs, files in os.walk(folder):
        for file in files:
            file_ = os.path.join(paths,file)
            if not os.path.isfile(file_):
                continue
            if file_ext:
                if not match(file_, file_ext):
                    continue
            file_size = str((os.path.getsize(file_)))
            all_files.append((file_size.zfill(12), file_))
    
    all_files.sort(reverse=True)

    text_file.write('List of all files inside folders and its subfolders in "{}".\n\n'.upper().format(folder))

    for size, file in all_files:
        size = format_size(size)
        line = '{} - {}\n'.format(size, file)
        text_file.write(line)
        record_type_n_size(file)

    summary = '*********** SUMMARY ***********'.center(53)
    text_file.write('\n\n' + summary + '\n\n')

    t_size = 'Total Size'.center(17).upper()
    n_files = 'Number of Files'.center(17).upper()
    file_ = 'File'.center(17).upper()
    text_file.write(t_size + '|' + n_files + '|' + file_ + '\n')

    file_dic = dict(sorted(file_dic.items(), key=operator.itemgetter(1), reverse=True))
      
    for file_type, value in file_dic.items():
        num, size = value
        size = format_size(str(size)).center(17)
        file_type = file_type.center(17)
        num = str(num).center(17)
        text_file.write(size + '|' + num + '|' + file_type + '\n')   