from distutils.core import setup

setup(
    # Application name:
    name="flask-eventics",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="CFPB",
    author_email="tech@cfpb.gov",

    # Packages
    packages=["flask_eventics",],

    # Include additional files into the package
    include_package_data=True,

    # Dependent packages (distributions)
    install_requires=[
        "flask",
    ],
)
