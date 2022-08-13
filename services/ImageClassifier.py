import glob
import exifread
import xml.etree.ElementTree as ET
import xml


def classify_images(src):
    red_images = []
    gre_images = []
    blu_images = []
    nir_images = []
    reg_images = []
    rgb_images = glob.glob(src + '/*.jpg')

    images = glob.glob(src + '/*.tif')
    for image in images:
        try:
            # first try and find image properties in xmp info, if not found will go and look for it on EXIF
            fd = open(image, errors="ignore")
            d = fd.read()
            xmp_start = d.find('<x:xmpmeta xmlns:x="adobe:ns:meta/"')
            xmp_end = d.find('</x:xmpmeta>')
            xmp_str = d[xmp_start:xmp_end+12]
            attempt1 = ET.fromstring(xmp_str)[0][0].get('{http://pix4d.com/camera/1.0}BandName')
            if attempt1 is not None:
                elem = attempt1
            else:
                elem = ET.fromstring(xmp_str)[0][0].find('{http://pix4d.com/camera/1.0}BandName').text
            if elem is not None:
                if elem == 'Green':
                    gre_images.append(image)
                    continue
                if elem == 'Blue':
                    blu_images.append(image)
                    continue
                if elem == 'RedEdge':
                    reg_images.append(image)
                    continue
                if elem == 'NIR':
                    nir_images.append(image)
                    continue
                if elem == 'Red':
                    red_images.append(image)
                    continue
        except Exception as e:
            # if xmp info cannot be parsed check EXIF info
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
