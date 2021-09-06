import glob
import cv2
import numpy as np
import json
import os
import matplotlib.pyplot as plt

VISION_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.dirname(VISION_PATH)
BASE_PATH = os.path.dirname(SERVER_PATH)
DATASET_PATH = os.path.join(BASE_PATH, 'dataset')
MODELS_PATH = os.path.join(BASE_PATH, 'models')

SRC_DATA = os.path.join(VISION_PATH, 'annotaion.json')
DST_DATA = os.path.join(MODELS_PATH, 'annotaion.json')


def load_data():
    with open(SRC_DATA) as f:
        data = json.loads(f.read())
    return data


data = load_data()

nodes = list(data.keys())
nodes.sort()
componenets = ['holder', 'dosing']


def npz_valid(npz_filename, roi_in, zero_in):
    if not os.path.isfile(npz_filename):
        return False
    npz = np.load(npz_filename, allow_pickle=True)
    return (npz.get('roi') == roi_in) and (npz.get('zero') == zero_in)


def prepare_frame(frame, roi, component):
    if component == 'dosing':
        x_downsample = 8
        y_downsample = 1
    elif component == 'holder':
        x_downsample = 1
        y_downsample = 8
    else:
        raise

    x0 = roi['x0']
    x1 = roi['x0'] + roi['dx']
    y0 = roi['y0']
    y1 = roi['y0'] + roi['dy']
    x_size = round(roi['dx'] / x_downsample)
    y_size = round(roi['dy'] / y_downsample)

    frame = frame[y0:y1, x0:x1, :]
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (x_size, y_size), interpolation=cv2.INTER_AREA)

    # plt.imshow(frame)
    # plt.show()
    # raise

    frame = frame.flatten()
    return frame


def main():
    for node in nodes:
        for component in componenets:
            roi = data[node][component + '_roi']

            for dataset_name in data[node][component]:
                IMAGES = []
                INDICES = []

                dataset_dict = data[node][component][dataset_name]
                path = DATASET_PATH + '/%s_%s_%s_192.168.44.%s' % (
                    component, node, dataset_name, node)
                npz_filename = path + '/data.npz'
                files = glob.glob(path + '/*.png')
                files.sort()
                fpr = int(files[-1].split('/')[-1].split('_')[0]) + 1
                zero = dataset_dict['zero']
                print(path, fpr)

                if npz_valid(npz_filename, roi, zero):
                    print('npz is valid')
                    continue

                for filename in files:
                    image = cv2.imread(filename)
                    image = prepare_frame(image, roi, component)
                    IMAGES.append(image)

                    index = int(filename.split('/')[-1].split('_')[0]) - zero
                    index = float(index % fpr) / fpr
                    INDICES.append(index)

                IMAGES = np.array(IMAGES)
                INDICES = np.array(INDICES)
                np.savez_compressed(path + '/data.npz',
                                    images=IMAGES, indices=INDICES, roi=roi, zero=zero)


if __name__ == '__main__':
    main()
