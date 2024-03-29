import cv2
import matplotlib.pyplot as plt
import numpy
import numpy as np
import os

from utils.Index import Index

orthophoto_path = '/multispectral/odm_orthophoto/odm_orthophoto'
rgb_orthophoto_path = '/rgb/odm_orthophoto/odm_orthophoto'


def check_images_missing(index_formula, red, nir, reg, gre, blue):
    red_missing = "red" in index_formula and red is None
    nir_missing = "nir" in index_formula and nir is None
    reg_missing = "reg" in index_formula and reg is None
    gre_missing = "gre" in index_formula and gre is None
    blue_missing = "blue" in index_formula and blue is None

    return red_missing or nir_missing or reg_missing or gre_missing or blue_missing


def calculate_index(project_path, indexes, custom_indexes, fig, ax):
    red_path = project_path + orthophoto_path + '_RED.tif'
    nir_path = project_path + orthophoto_path + '_NIR.tif'
    reg_path = project_path + orthophoto_path + '_REG.tif'
    gre_path = project_path + orthophoto_path + '_GRE.tif'
    blue_path = project_path + orthophoto_path + '_BLU.tif'

    print("reading multispectral images")
    red_present, red_img = read_img(red_path)
    nir_present, nir_img = read_img(nir_path)
    reg_present, reg_img = read_img(reg_path)
    gre_present, gre_img = read_img(gre_path)
    blue_present, blue_img = read_img(blue_path)

    red = convert_to_array(red_img, red_present)
    nir = convert_to_array(nir_img, nir_present)
    reg = convert_to_array(reg_img, reg_present)
    gre = convert_to_array(gre_img, gre_present)
    blue = convert_to_array(blue_img, blue_present)

    check = np.logical_and.reduce(get_check(red, nir, reg, gre, blue))

    result = {}
    paths = {}
    for index in indexes:
        index_png_path = project_path + '/index_' + index + '.png'
        index_npy_path = project_path + '/index_' + index + '.npy'
        if os.path.exists(index_png_path) and os.path.exists(index_npy_path):
            result[index] = None
            paths[index] = {
                'img': index_png_path,
                'vector': index_npy_path
            }
        else:
            if not check_images_missing(Index[index].value, red, nir, reg, gre, blue):
                val = get_index(index, check, red, nir, reg, gre, blue)
                result[index] = val
                paths[index] = {
                    'img': index_png_path,
                    'vector': index_npy_path
                }
            else:
                result[index] = None
                paths[index] = None

    for custom_index in custom_indexes:
        if not check_images_missing(custom_index['formula'], red, nir, reg, gre, blue):
            val = get_custom_index(custom_index['formula'], check, red, nir, reg, gre, blue)
            result[custom_index['name']] = val
            paths[custom_index['name']] = {
                    'img': project_path + '/index_' + custom_index['name'] + '.png',
                    'vector': project_path + '/index_' + custom_index['name'] + '.npy'
                }
        else:
            result[custom_index['name']] = None
            paths[custom_index['name']] = None

    for key in result:
        if result[key] is not None:
            create_heatmap(result[key],
                           project_path + '/index_' + key + '.png',
                           True,
                           3000,
                           fig,
                           ax)
            numpy.save(project_path + '/index_' + key + '.npy', result[key])

    return paths


def check_rgb_images(paths):
    all_rgb_present_in_multispectral = True
    for image in paths:
        all_rgb_present_in_multispectral = all_rgb_present_in_multispectral and os.path.exists(image)
    return all_rgb_present_in_multispectral


def read_img(img):
    if img is not None and os.path.exists(img):
        return True, cv2.imread(img, cv2.IMREAD_UNCHANGED)
    return False, None


def convert_to_array(img, present, index=0):
    return np.array(img, dtype=float)[:, :, index] * 256 if present else None


def get_check(red=None, nir=None, reg=None, gre=None, blue=None):
    logical_and = []
    if red is not None:
        logical_and.append(red > 1)
    if nir is not None:
        logical_and.append(nir > 1)
    if reg is not None:
        logical_and.append(reg > 1)
    if gre is not None:
        logical_and.append(gre > 1)
    if blue is not None:
        logical_and.append(blue > 1)
    return logical_and


def get_index(index_name, check, red, nir, reg, gre, blue):
    try:
        return np.where(check, eval(Index[index_name].value), -999)
    except (NameError, SyntaxError) as e:
        return None


def get_custom_index(custom_index, check, red, nir, reg, gre, blue):
    try:
        return np.where(check, eval(custom_index), -999)
    except (NameError, SyntaxError) as e:
        return None


def create_heatmap(arr: np.ndarray, output, save, dpi, fig, ax, min_val=-1, max_val=1):
    masked_data = np.ma.masked_where((arr == 0) | (arr == -999), arr)
    ax.imshow(arr, cmap='gray', alpha=0)
    ax.imshow(masked_data, cmap='RdYlGn', interpolation='none', vmin=min_val, vmax=max_val)

    plt.axis('off')
    if save:
        plt.savefig(output, bbox_inches='tight', dpi=dpi, transparent=True)
    else:
        plt.show()
    plt.cla()


def get_zone_above_threshold(src, threshold_max, threshold_min, fig, ax):
    out = src[:-3] + '_threshold_' + str(threshold_min) + '_' + str(threshold_max) + '.png'
    array = numpy.load(src)
    array[array == 0] = -999
    array[array >= threshold_max] = -999
    array[array <= threshold_min] = -999
    array[(array > threshold_min) & (array < threshold_max)] = 1
    create_heatmap(array, out, True, 3000, fig, ax, min_val=1, max_val=1)
    return out


def only_rgb_index(index):
    return ("red" in index or "gre" in index or "blue" in index) and "nir" not in index and "reg" not in index
