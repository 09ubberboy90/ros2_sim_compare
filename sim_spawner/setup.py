from setuptools import setup

package_name = 'sim_spawner'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Florent Audonnet',
    maintainer_email='2330834a@student.gla.ac.uk',
    description='spawn object in both simulation and run the services to get their positions',
    license='BSD 3-Clause License',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "webots_spawner = sim_spawner.webots_spawner:main",
            "webots_throw_spawner = sim_spawner.webots_throw_spawner:main",
            "gazebo_spawner = sim_spawner.gazebo_spawner:main",
            "gazebo_throw_spawner = sim_spawner.gazebo_throw_spawner:main",

        ],
    },
)
