# encoding: utf-8
import os
import sys

def check_type(input_param):
    try:
        int_value = int(input_param)
        print(r'{} is int type'.format(input_param))
        return True
    except ValueError:
        if isinstance(input_param, str):
            print("intput is str")
            return False
        elif isinstance(input_param, int):
            print("intput is int")
            return True
        else:
            print("Please input a valid parameter type.")


def find_parameter_key_index(line, para_map):
    for key in para_map:
        if line.startswith(key + ' '):  # 检查行首是否有符合键值+空格的开头部分
            # print("find key:{} with len:{}".format(key,len(key) + 1), type(len(key) + 1))            
            return len(key) + 1  # 如果找到匹配，则返回其位置（下标）的加一位置，用于之后的分割操作
    return None  

def find_str_no_empty(line):
    index = line.find(' ')
    if index != -1:  # 如果找到了空格
        return line[:index]
    else:
        return line

def check_match_in_map(para_map, str_to_check):
    if str_to_check in para_map:
        return True  
    else:
        return False  
    
    
def para_map_gen(trigger_style, rec_len, acq_time, threshold, filename):
    if trigger_style == 'ext':
        para_map = {
            'OUTFILE_PATH': '/mnt/data/PMT/R8520_406/',
            #'OUTFILE_PATH': '/mnt/data/TPC/',
            'OUTFILE_NAME': 'lv2415_lv2414_20241126_12DB_LED_combine_1p7v_850mv_1p36v_680mv_5us_50hz_run0',
            'EXTERNAL_TRIGGER': 'ACQUISITION_ONLY',
            'SELF_TRIGGER': 'NO',
            'TRG_THRESHOLD': 20,
            'RECORD_LENGTH': 40,  ## 175 for 5us
            'ACQ_TIME': 480
        }
        if check_type(rec_len) == True:
            para_map['RECORD_LENGTH'] = rec_len
        elif check_type(rec_len) == False:                
            print('record length shold be int, number * 10')
            sys.exit()
        if check_type(acq_time) == True:
            para_map['ACQ_TIME'] = acq_time
        elif check_type(acq_time) == False:
            print('record length shold be int unit in seconds')
            sys.exit()
        if check_type(threshold) == True:
            para_map['TRG_THRESHOLD'] = threshold
        else:
            print('threshold should be int, 20 ADC for example')
            sys.exit()           
        if check_type(filename) == False:
            para_map['OUTFILE_NAME'] = filename
        else:
            print('output filename should be string')
            sys.exit()
        #return para_map
    elif trigger_style == 'self':
        para_map = {
            #'OUTFILE_PATH': '/mnt/data/TPC/',
            'OUTFILE_PATH': '/mnt/data/PMT/R8520_406/',
            'OUTFILE_NAME': 'lv2415_lv2414_20241118_darkrate_run0',
            'EXTERNAL_TRIGGER': 'DISABLE',
            'SELF_TRIGGER': 'YES',
            'RECORD_LENGTH': 40,
            'TRG_THRESHOLD': 20,
            'ACQ_TIME': 480
        }
        if check_type(rec_len) == True:
            para_map['RECORD_LENGTH'] = rec_len
        elif check_type(rec_len) == False:
            print('record length shold be int, number * 10')
            sys.exit()
        if check_type(threshold) == True:
            para_map['TRG_THRESHOLD'] = threshold
        elif check_type(threshold) == Fasle:
            print('threshold should be int, 20 ADC for example')
            sys.exit()
        if check_type(acq_time) == True:
            para_map['ACQ_TIME'] = acq_time
        elif check_type(acq_time) == False:
            print('acq_time should be int unit in second ')
            sys.exit()
        if check_type(filename) == False:
            para_map['OUTFILE_NAME'] = filename
        elif check_type(filename) == Ture: 
            print('filename should be string')
            sys.exit()
    return para_map


def replace_parameters_in_config(para_map, config_file):
    print("Writing new configuration file...")
    with open(config_file, 'r') as file:
        lines = file.readlines()
    new_lines = [] 
    for line in lines:
        # 跳过空行        
        if line.strip() == '':   
            continue  
        # 如果这一行是带 '#' 的注释行，则直接保留到新文件中
        if line.strip().startswith('#'):
            new_lines.append(line)  # 直接添加到新文件中的列表中
            continue  # 跳过进一步的参数替换检查，因为注释行不参与参数替换
        
        key_index = find_parameter_key_index(line, para_map)  # 查找行首至空格处是否存在键值并获取索引
        if key_index is not None:
            key, value = line.split(' ', 1)  
            new_line = str(key) + " " + str(para_map[key]) + "\n"
            new_lines.append(new_line)  # 将新生成的行加入到新文件中
            print(r'writing >>>> {}'.format(new_line))
            continue
        else:  # 如果没有找到匹配的键进行替换，则保留原始行（包含注释）
            new_lines.append(line)
      
    with open('configure_new.txt', 'w') as newfile: 
        for line in new_lines:
            newfile.write(line)  # 将每行内容写入新文件
        newfile.write('\n')   
        
    print("New configuration file has been written to 'configure_new.txt'.")
                                                    

def main():
    if len(sys.argv) != 6:        
        print("USAGE: python write_config.py ext 40 480 file_name")
        print('USAGE: python write_config.py trig_style[self] rec_len[int] acq_time[int] threshold[int] file_name[str] ')                
        sys.exit(1)
    config_file_path = './DAW_Config.txt'
    #config_file_path = '/etc/DAW_Demo/DAW_Config.txt'
    trigger_style = sys.argv[1]
    rec_len = sys.argv[2]
    acq_time = sys.argv[3]
    threshold = sys.argv[4]
    filename = sys.argv[5]
    para_map = para_map_gen(trigger_style, rec_len, acq_time, threshold, filename)
    replace_parameters_in_config(para_map, config_file_path)

if __name__ == "__main__":
    main()
