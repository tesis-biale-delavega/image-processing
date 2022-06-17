import glob
import exifread


def classify_images(src):
    file_types = ('/*.jpg', '/*.tif')
    rgb_images = []
    red_images = []
    gre_images = []
    blu_images = []
    nir_images = []
    reg_images = []

    for file_type in file_types:
        images = glob.glob(src + file_type)
        for image in images:
            tags = exifread.process_file(open(image, 'rb'))
            try:
                wavelength = int(str(tags.get('Image ImageDescription'))[:-3])
                if 450 < wavelength < 485:
                    blu_images.append(image)
                if 500 < wavelength < 565:
                    gre_images.append(image)
                if 625 < wavelength < 700:
                    red_images.append(image)
                if 700 < wavelength < 780:
                    reg_images.append(image)
                if 780 < wavelength < 2500:
                    nir_images.append(image)

            except ValueError:
                rgb_images.append(image)

    return {
        'rgb_images': rgb_images,
        'red_images': red_images,
        'gre_images': gre_images,
        'blu_images': blu_images,
        'nir_images': nir_images,
        'reg_images': reg_images
    }
