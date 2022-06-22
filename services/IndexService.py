import cv2
import matplotlib.pyplot as plt
import numpy
import numpy as np
import os
import enum


class Index(enum.Enum):
    ndvi = "(nir - red) / (nir + red)"
    savi = "(1.5 * (nir - red)) / (nir + red + 0.5)"
    ndwi = "(gre - nir) / (gre + nir)"


def calculate_index(project_path, indexes, custom_indexes, fig, ax):
    red_path = project_path + '/odm_orthophoto_RED.tif'
    nir_path = project_path + '/odm_orthophoto_NIR.tif'
    reg_path = project_path + '/odm_orthophoto_REG.tif'
    gre_path = project_path + '/odm_orthophoto_GRE.tif'
    blue_path = project_path + '/odm_orthophoto_BLU.tif'  # TODO check blue file

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
        val = get_index(index, check, red, nir, reg, gre, blue)
        result[index] = val
        paths[index] = project_path + '/index_' + index + '.png'

    for custom_index in custom_indexes:
        val = get_custom_index(custom_index['formula'], check, red, nir, reg, gre, blue)
        result[custom_index['name']] = val
        paths[custom_index['name']] = project_path + '/index_' + custom_index['name'] + '.png'

    for key in result:
        create_heatmap(result[key], project_path + '/index_' + key + '.png', True, 4000, fig, ax)
        numpy.save(project_path + '/index_' + key + '.npy', result[key])

    return paths


def read_img(img):
    if img is not None and os.path.exists(img):
        return True, cv2.imread(img, cv2.IMREAD_UNCHANGED)
    return False, None


def convert_to_array(img, present):
    return np.array(img, dtype=float)[:, :, 0] * 256 if present else None


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


def create_heatmap(arr: np.ndarray, output, save, dpi, fig, ax):
    masked_data = np.ma.masked_where(arr == 0, arr)
    ax.imshow(arr, cmap='gray', alpha=0)
    ax.imshow(masked_data, cmap='viridis', interpolation='none', vmax=1, vmin=-1)

    plt.axis('off')
    if save:
        plt.savefig(output, bbox_inches='tight', dpi=dpi, transparent=True)
    else:
        plt.show()


def get_zone_above_threshold(src, threshold_max, threshold_min, out, fig, ax):
    array = numpy.load(src)
    array[array >= threshold_max] = 0
    array[array <= threshold_min] = 0
    array[(array > threshold_min) & (array < threshold_max)] = 1
    create_heatmap(array, out, True, 4000, fig, ax)
    return out
