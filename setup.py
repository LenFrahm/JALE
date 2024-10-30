from setuptools import find_packages, setup

setup(
    name="ALEpy",  # Unique name for your package
    version="0.1.0",  # Initial version
    description="Package allowing users to run Activation Likelihood Estimation Meta-Analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lennart Frahm",
    author_email="l.frahm@mailbox.org",
    url="https://github.com/LenFrahm/ALEpy",
    license="MIT",
    packages=find_packages(),  # Automatically find packages in the project
    install_requires=[  # List of dependencies
        "customtkinter>=5.2.2",
        "joblib>=1.3.2",
        "nibabel>=5.3.2",
        "numpy>=2.1.2",
        "pandas>=2.2.3",
        "pytest>=8.0.0",
        "PyYAML>=6.0.2",
        "scipy>=1.14.1",
        "xgboost>=2.1.2",
    ],
    classifiers=[  # Classifiers help users find your project
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)