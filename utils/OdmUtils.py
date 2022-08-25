def get_multispectral_config(main_band):
    return {
        'fast-orthophoto': True,
        'orthophoto-cutline': False,  # check results, if this cuts too much surface
        'skip-3dmodel': True,
        'skip-report': True,  # Can be useful
        'max-concurrency': 8,
        'pc-quality': 'medium',  # default is medium
        'feature-quality': 'high',  # default is high
        'dem-decimation': 10,  # default is 1
        'radiometric-calibration': 'camera',
        'primary-band': main_band,
        'verbose': True,
        'debug': True
    }


def get_rgb_config():
    return {
        'fast-orthophoto': True,
        'orthophoto-png': True,
        'orthophoto-cutline': True,  # check results, if this cuts too much surface
        'skip-3dmodel': True,
        'skip-report': True,  # Can be useful
        'max-concurrency': 8,  # default is 4
        'pc-quality': 'medium',  # default is medium
        'feature-quality': 'high',  # default is high
        'dem-decimation': 10,  # default is 1
        'auto-boundary': True,
        'verbose': True,
        'debug': True
    }
