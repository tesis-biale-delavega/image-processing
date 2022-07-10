import exifread
import glob
import json


def avg_coords(img_paths, output_path):
    multispectral = glob.glob(img_paths + '/*.tif')
    filt = list(filter(lambda x: x[:-4][-3:] == 'GRE', multispectral))
    total_imgs = 0
    alt_sum = 0
    lat_sum = 0
    long_sum = 0
    for img in filt:  # if this does not work for other drones, can use ODM output json files
        tags = exifread.process_file(open(img, 'rb'))
        lat = str(tags['GPS GPSLatitude'])
        lat_list = lat.strip('][').split(', ')
        lat_list.append(str(tags['GPS GPSLatitudeRef']))
        lat_sum = lat_sum + convert(lat_list)

        long = str(tags['GPS GPSLongitude'])
        long_list = long.strip('][').split(', ')
        long_list.append(str(tags['GPS GPSLongitudeRef']))
        long_sum = long_sum + convert(long_list)

        alt_sum = alt_sum + eval(str(tags['GPS GPSAltitude']))
        total_imgs = total_imgs + 1

    avg_lat = lat_sum / total_imgs
    avg_long = long_sum / total_imgs
    avg_alt = alt_sum / total_imgs
    data = {
        'lat': avg_lat,
        'long': avg_long,
        'alt': avg_alt
    }
    with open(output_path + '/avg_coordinates.json', 'w') as f:
        json.dump(data, f)
    return avg_lat, avg_long, avg_alt


def convert(tude):
    multiplier = 1 if tude[-1] in ['N', 'E'] else -1
    return multiplier * sum(float(float(eval(x))) / 60 ** n for n, x in enumerate(tude[:-1]))