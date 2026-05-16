import os
import pickle
# from datetime import datetime

DATA_DIR = './data'

INPUTS_TRAIN_FILE = 'inputs_train.pkl'
INPUTS_VALID_FILE = 'inputs_valid.pkl'
OUTPUTS_TRAIN_FILE = 'outputs_train.pkl'
OUTPUTS_VALID_FILE = 'outputs_valid.pkl'

file_prefix = 'xxx'

def print_data_info(file_name):
    with open(file_name, 'rb') as file:
        data = pickle.load(file)
    # print(datetime.fromtimestamp(data[0][0]).strftime('%Y-%m-%d %H:%M:%S'))        
    print(data[0])
    print(data[1])
    print(data[2])
    print(data[-3])
    print(data[-2])
    print(data[-1])
    print(len(data))

print_data_info('./timeshots/timeshots.pkl')
print_data_info(os.path.join(DATA_DIR, f'{file_prefix}_{INPUTS_TRAIN_FILE}'))
print_data_info(os.path.join(DATA_DIR, f'{file_prefix}_{INPUTS_VALID_FILE}'))
print_data_info(os.path.join(DATA_DIR, f'{file_prefix}_{OUTPUTS_TRAIN_FILE}'))
print_data_info(os.path.join(DATA_DIR, f'{file_prefix}_{OUTPUTS_VALID_FILE}'))
