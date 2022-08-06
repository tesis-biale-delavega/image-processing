import exifread
import glob
import json


def avg_coords(img_paths, output_path):
    multispectral = glob.glob(img_paths + '/*.tif')
    filt = list(filter(lambda x: x[:-4][-3:] == 'GRE', multispectral))
    avg_lat, avg_long, avg_alt, points = calculate_points(filt)

    rgb = glob.glob(img_paths + '/*.jpg')
    avg_rgb_lat, avg_rgb_long, avg_rgb_alt, rgb_points = calculate_points(rgb)

    data = {
        'avg_lat': avg_lat,
        'avg_long': avg_long,
        'avg_alt': avg_alt,
        'points': points,
        'avg_rgb_lat': avg_rgb_lat,
        'avg_rgb_long': avg_rgb_long,
        'avg_rgb_alt': avg_rgb_alt,
        'rgb_points': rgb_points
    }
    with open(output_path + '/avg_coordinates.json', 'w') as f:
        json.dump(data, f)
    return data


def calculate_points(imgs):
    total_imgs = 0
    alt_sum = 0
    lat_sum = 0
    long_sum = 0
    max_lat = -9999
    min_lat = 9999
    max_long = -9999
    min_long = 9999
    for img in imgs:  # if this does not work for other drones, can use ODM output json files
        tags = exifread.process_file(open(img, 'rb'))
        lat = str(tags['GPS GPSLatitude'])
        lat_list = lat.strip('][').split(', ')
        lat_list.append(str(tags['GPS GPSLatitudeRef']))
        current_lat = convert(lat_list)
        if current_lat > max_lat:
            max_lat = current_lat
        if current_lat < min_lat:
            min_lat = current_lat
        lat_sum = lat_sum + current_lat

        long = str(tags['GPS GPSLongitude'])
        long_list = long.strip('][').split(', ')
        long_list.append(str(tags['GPS GPSLongitudeRef']))
        current_long = convert(long_list)
        long_sum = long_sum + current_long
        if current_long > max_long:
            max_long = current_long
        if current_long < min_long:
            min_long = current_long

        alt_sum = alt_sum + eval(str(tags['GPS GPSAltitude']))
        total_imgs = total_imgs + 1

    avg_lat = lat_sum / total_imgs
    avg_long = long_sum / total_imgs
    avg_alt = alt_sum / total_imgs
    points = [
        [min_long, min_lat],
        [min_long, max_lat],
        [max_long, min_lat],
        [max_long, max_lat]
    ]
    return avg_lat, avg_long, avg_alt, points


def convert(tude):
    multiplier = 1 if tude[-1] in ['N', 'E'] else -1
    return multiplier * sum(float(float(eval(x))) / 60 ** n for n, x in enumerate(tude[:-1]))