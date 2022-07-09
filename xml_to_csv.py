from argparse import ArgumentParser
from lxml import etree as et
import pandas as pd
import os.path as op
import glob
import sys



def list_file(path):
    if not op.isdir(path):
            print('\n-------Missing directory. Might be a case of incorrect path/folder name. Please check.-------')
            sys.exit()
    else:
        files =  glob.glob(op.join(path, '*.XML'))
        if len(files) < 1:
            print('\n-------No XML files found, please check path directory or check folder-------')
            sys.exit()
    return files


def get_tree(file):
    print('\rPreparing files now...', end='                        ')
    tree = et.parse(file, et.XMLParser(ns_clean=True, recover=True))
    return tree


def get_root(tree):
    root = tree.getroot()
    return root


def chanel_list(root):
    channel_list = None

    if root.find('.//CHANNEL-SET') is not None:
        channel_list = ['CH' + elem.attrib['name'] for elem in root.find('.//CHANNEL-SET').findall('CHANNEL')]
    else:
        channel_list = ['CH' + root.find('.//CHANNEL').attrib['name']]

    return channel_list


# collect all cpoint attribute whether id, date or time
def list_cpoint_attrib(root, attrib):
    attrib_list = [elem.attrib[attrib] for elem in root.findall('.//CPOINT')]
    return attrib_list


# collect all coordinates
def gps_coord(root, longlat):
    coord_list = [elem.attrib[longlat] for elem in root.findall('.//GPS')]
    return coord_list


def list_status(root):
    stats = [elem.attrib['value'] for elem in root.findall('.//STATUS')]
    return stats


# collecting all power values of CHANNEL tags
# by finding all CHANNEL element and
# finally filtering those with attribute name('15' or '18'....)
def list_power(root, channel):
    power_list = [elem.find('.//POWER').attrib['value'] for elem in root.findall('.//CHANNEL') 
                                                        if elem.attrib['name'] == channel and 
                                                            elem.getparent().tag =='CHANNEL-SET']
    return power_list


def list_measures(root, measures):
    measures_list = [elem.attrib['value'] for elem in root.findall('.//{}'.format(measures))]
    return measures_list


def dict_update(dict, channel, measure_list, measure):
    column_name = {'power'  : channel + ' - {} (dBuV)'.format(measure.upper()),
                   'status' : channel + ' - {}'.format(measure.upper()),
                   'cn'     : channel + ' - {} (dB)'.format(measure.upper()),
                   'offset' : channel + ' - {} (kHZ)'.format(measure.upper()),
                   'mer'    : channel + ' - {} (dB)'.format(measure.upper()),
                   'cber'   : channel + ' - {}'.format(measure.upper()),
                   'vber'   : channel + ' - {}'.format(measure.upper()),
                   'lm'     : channel + ' - {} (dB)'.format(measure.upper())
                   }
    dict.update({column_name[measure]:measure_list})


def xml_to_dictionary(tree):

    root = get_root(tree)
    
    measurements = ['status', 'cn', 'offset', 'mer', 'cber', 'vber', 'lm']
    info = ['TEST POINT', 'DATE (YYYY-MM-DD)', 'TIME (HH:MM:SS)']
    cp_attribute = ['id', 'date', 'time']
    longlat = ['latitude', 'longitude']

    # dictionary
    d = {}

    # populate the dictionary with cpoint attributes(id, date and time)
    for col_name, attrib in zip(info, cp_attribute):
        d[col_name] = list_cpoint_attrib(root, attrib)
    
    # populate coordinates
    for coord in longlat:
        d[coord.upper()] = gps_coord(root, coord)
   
    list_ch = chanel_list(root)                                     # this list contains a string of channel(e.g. 'CH1', 'CH2'... 'CH50')
    main_CH = list_ch[0]
    
    if len(list_ch) > 1:
        power_list = list_power(root,main_CH[2:])
        dict_update(d, main_CH, power_list, 'power')

        for measure in measurements:
            measure_list = list_measures(root,measure.upper())
            dict_update(d, main_CH, measure_list, measure)

        for ch in list_ch[1:]:
            power_list = list_power(root,ch[2:])
            dict_update(d, ch, power_list, 'power')

    else:
        for measure in ['power'] + measurements:
            measure_list = list_measures(root,measure.upper())
            dict_update(d, main_CH, measure_list, measure)

    return d


def df_split(df):
        stat = [stat for stat in df.columns if 'STATUS' in stat][0]
        MPEG_TS_locked = df.loc[df[stat]=='MPEG2 TS locked']
        No_Signal = df.loc[df[stat]=='No signal received']
        return MPEG_TS_locked, No_Signal


def to_df(d):
    try:
        df = pd.DataFrame(d)
    except ValueError as e:
        missing_measurements = []
        for k,v in d.items():
            if len(v) == 0:
                missing_measurements.append(k)
        return missing_measurements
    return df


def to_csv(xml_d_list, name_list, stat=False):
    path, _ = op.split(name_list[0])

    df_list = [to_df(xml_d) for xml_d in xml_d_list]
    
    if not stat:
        for df, name in zip(df_list, name_list):
            if isinstance(df, list):
                print("""\nThe file named {0} is inconsistent with the rest.\nPlease open the xml file in a notepad. It may not have the following {1}.""".format(op.split(name)[1] + '.csv', str(df)))
                continue
            df.to_csv(name + '.csv', index=False) 
    else:
        path = op.split(name_list[0])[0]
        df_list = [df for df in df_list if not isinstance(df, list)]
        df = pd.concat(df_list)
        MPEG_TS_locked, No_Signal = df_split(df)
        MPEG_TS_locked.to_csv(op.join(path, 'MPEG_TS_locked.csv'), index=False)
        No_Signal.to_csv(op.join(path, 'No_Signal.csv'), index=False)


def progress_bar(progress, total):
    percent = 100 * (progress /float(total))
    bar = '█' * int(percent) + '-' * 100 - int(percent)
    print(f'\r|{bar}|{percent:.2f}%', end='\r')
    

def main(path, stat):

    xml_list = list_file(path)
    xml_tree_list = [get_tree(xml) for xml in xml_list]
    xml_d_list = [xml_to_dictionary(tree) for tree in xml_tree_list]
    csv_fnames = [file.rsplit('.', 1)[0] for file in xml_list]
    to_csv(xml_d_list, csv_fnames, stat)
    print('\rDone', end='                           ')


if __name__ == '__main__':

    # Create parser
    my_parser = ArgumentParser(prog='xml_to_csv',
                            usage='Convert to CSV XML file output from PROMAX Ranger Explorer',
                            description='Command Line Application that converts XML files to CSV. This will take\n\
                                        a folder with xml files and convert them to csv which all files can be consolidated as one unlike in the\n\
                                        PROMAX website where it takes/convert one by one. You can visit \n"https://www.promax.es/tools/kml-generator/".\n\
                                        \n'
                            )

    # Add the arguments
    my_parser.add_argument('path', type=str, help='the path to the folder containing XML files')
    my_parser.add_argument('-rip', '--rip_no_signal', action='store_true', help='separate the MPEG TS status to be extracted from the XML file.\
                                                                                \nNo Signal received if TS unlocked')

    # Excecute the parse_args method
    args = my_parser.parse_args()

    main(args.path, args.rip_no_signal)