from setuptools import find_packages, setup

package_name = 'turtle_eater'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='senthilnathan',
    maintainer_email='senthilnathan@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turtle_breeder = turtle_eater.turtle_breeder:main',
            'turtle_eater = turtle_eater.eater:main',
            'claude_breeder = turtle_eater.claude_breeder:main',
        ],
    },
)
