import cv2
import matplotlib.pyplot as plt
import numpy
import numpy as np
import os

from utils.Index import Index

orthophoto_path = '/multispectral/odm_orthophoto/odm_orthophoto'
rgb_orthophoto_path = '/rgb/odm_orthophoto/odm_orthophoto'


def check_images_missing(index_formula, red, nir, reg, gre, blue, red_alternative, gre_alternative, blue_alternative):
    red_missing = "red" in index_formula and red is None
    nir_missing = "nir" in index_formula and nir is None
    reg_missing = "reg" in index_formula and reg is None
    gre_missing = "gre" in index_formula and gre is None
    blue_missing = "blue" in index_formula and blue is None

    index_rgb = only_rgb_index(index_formula)
    rgb_missing = index_rgb and red_alternative is None and gre_alternative is None and blue_alternative is None

    if index_rgb:
        return rgb_missing
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

    any_all_rgb_index = list(map(only_rgb_index, map(lambda x: Index[x].value, indexes))) + list(map(only_rgb_index, map(lambda x: x['formula'], custom_indexes)))
    should_read_rgb = any_all_rgb_index.count(True) > 0
    should_read_multispectral = any_all_rgb_index.count(False) > 0
    red, nir, reg, gre, blue = None, None, None, None, None
    check = None

    red_alternative, gre_alternative, blue_alternative = None, None, None
    alternative_check = None

    if should_read_rgb:
        print("reading rgb images")
        red_alternative_present, red_alternative_img = read_img(red_alternative_path)
        gre_alternative_present, gre_alternative_img = read_img(gre_alternative_path)
        blue_alternative_present, blue_alternative_img = read_img(blue_alternative_path)

        red_alternative = convert_to_array(red_alternative_img, red_alternative_present, 2)
        gre_alternative = convert_to_array(gre_alternative_img, gre_alternative_present, 1)
        blue_alternative = convert_to_array(blue_alternative_img, blue_alternative_present, 0)

        alternative_check = np.logical_and.reduce(get_check(red_alternative, None, None, gre_alternative, blue_alternative))

    if should_read_multispectral:
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
        if not check_images_missing(Index[index].value, red, nir, reg, gre, blue, red_alternative, gre_alternative, blue_alternative):
            val = get_index(index, check, red, nir, reg, gre, blue) if not only_rgb_index(Index[index].value) \
                else get_index(index, alternative_check, red_alternative, nir, reg, gre_alternative, blue_alternative)
            result[index] = val
            paths[index] = {
                'img': project_path + '/index_' + index + '.png',
                'vector': project_path + '/index_' + index + '.npy'
            }
        else:
            result[index] = None
            paths[index] = None

    for custom_index in custom_indexes:
        if not check_images_missing(custom_index['formula'], red, nir, reg, gre, blue, red_alternative, gre_alternative, blue_alternative):
            val = get_custom_index(custom_index['formula'], check, red, nir, reg, gre, blue) if not only_rgb_index(custom_index['formula']) \
                else get_custom_index(custom_index['formula'], alternative_check, red_alternative, nir, reg, gre_alternative, blue_alternative)
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
    array[array >= threshold_max] = 0
    array[array <= threshold_min] = 0
    array[(array > threshold_min) & (array < threshold_max)] = 1
    create_heatmap(array, out, True, 3000, fig, ax, min_val=1, max_val=1)
    return out


def only_rgb_index(index):
    return ("red" in index or "gre" in index or "blue" in index) and "nir" not in index and "reg" not in index
