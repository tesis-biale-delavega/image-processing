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
    red_alternative_path = project_path + rgb_orthophoto_path + '.tif'
    nir_path = project_path + orthophoto_path + '_NIR.tif'
    reg_path = project_path + orthophoto_path + '_REG.tif'
    gre_path = project_path + orthophoto_path + '_GRE.tif'
    gre_alternative_path = project_path + rgb_orthophoto_path + '.tif'
    blue_path = project_path + orthophoto_path + '_BLU.tif'  # TODO check blue file
    blue_alternative_path = project_path + rgb_orthophoto_path + '.tif'

    red_present, red_img, is_red_alternative = read_img(red_path, red_alternative_path)
    nir_present, nir_img, is_nir_alternative = read_img(nir_path)
    reg_present, reg_img, is_reg_alternative = read_img(reg_path)
    gre_present, gre_img, is_gre_alternative = read_img(gre_path, gre_alternative_path)
    blue_present, blue_img, is_blue_alternative = read_img(blue_path, blue_alternative_path)

    red = convert_to_array(red_img, red_present, 2 if is_red_alternative else 0)
    nir = convert_to_array(nir_img, nir_present)
    reg = convert_to_array(reg_img, reg_present)
    gre = convert_to_array(gre_img, gre_present, 1 if is_gre_alternative else 0)
    blue = convert_to_array(blue_img, blue_present, 0 if is_blue_alternative else 0)

    check = np.logical_and.reduce(get_check(red, nir, reg, gre, blue))
    result = {}
    paths = {}
    for index in indexes:
        if not check_images_missing(Index[index].value, red, nir, reg, gre, blue):
            val = get_index(index, check, red, nir, reg, gre, blue)
            result[index] = val
            paths[index] = {
                'img': project_path + '/index_' + index + '.png',
                'vector': project_path + '/index_' + index + '.npy'
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
                           4000,
                           fig,
                           ax)
            numpy.save(project_path + '/index_' + key + '.npy', result[key])

    return paths


def read_img(img, alternative_path=None):
    if img is not None and os.path.exists(img):
        return True, cv2.imread(img, cv2.IMREAD_UNCHANGED), False
    if alternative_path is not None and os.path.exists(alternative_path):
        return True, cv2.imread(alternative_path, cv2.IMREAD_UNCHANGED), True
    return False, None, False


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


def get_zone_above_threshold(src, threshold_max, threshold_min, fig, ax):
    out = src[:-3] + '_threshold_' + str(threshold_min) + '_' + str(threshold_max) + '.png'
    array = numpy.load(src)
    array[array >= threshold_max] = 0
    array[array <= threshold_min] = 0
    array[(array > threshold_min) & (array < threshold_max)] = 1
    create_heatmap(array, out, True, 4000, fig, ax)
    return out
