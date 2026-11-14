import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'decision_making_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # BT XML (Groot2 로 편집)
        (os.path.join('share', package_name, 'trees'), glob('trees/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hhk-laptop',
    maintainer_email='whaihong@g.skku.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motion_planner_node = decision_making_pkg.motion_planner_node:main',
            'path_planner_node = decision_making_pkg.path_planner_node:main',
            'bt_planner_node = decision_making_pkg.bt_planner_node:main',
        ],
    },
)