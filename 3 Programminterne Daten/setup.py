# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name="rpctools",
    version="1.0.3",

    packages=find_packages('.', exclude=['ez_setup']),
    #namespace_packages=['rpctools'],

    package_dir={'': '.'},
    include_package_data=True,
    zip_safe=False,
    data_files=[
        ],
)
