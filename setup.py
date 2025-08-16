from setuptools import setup, find_packages

setup(
    name="motion-event",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gpiozero>=1.6.0",
        "sqlalchemy>=2.0.0",
        "schedule>=1.2.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
    author="Zheng Luo",
    description="A motion detection system that captures events and stores them in a database",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
