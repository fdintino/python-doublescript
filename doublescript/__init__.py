import pkg_resources

try:
    __version__ = pkg_resources.get_distribution('python-doublescript').version
except pkg_resources.DistributionNotFound:
    __version__ = None
