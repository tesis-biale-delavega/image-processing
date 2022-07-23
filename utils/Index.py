import enum


class Index(enum.Enum):
    dvi = "nir - red"
    ndvi = "(nir - red) / (nir + red)"
    ndre = "(nir - reg) / (nir + reg)"
    evi = "(nir - red) / (nir + 6 * red - 7.5 * blue + 1)"
    osavi = "(nir - red) / (nir + red + 0.16)"
    savi = "(1.5 * (nir - red)) / (nir + red + 0.5)"
    vari = "(gre - red) / (gre + red - blue)"
    arvi = "(nir - 2 * red + blue) / (nir + 2 * red + blue)"
    ndwi = "(gre - nir) / (gre + nir)"
    sipi = "(nir - blue) / (nir - red)"
    ari1 = "(1 / gre) - (1 / reg)"
