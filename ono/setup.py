"""
sudo apt-get install python-apt python-psycopg2

python3 -m pip install .
"""
import setuptools

PANDAS_VER = "2.1.1"

setuptools.setup(
    name="NER client",
    version="0.1.1",
    author="Roman Maliushkin",
    author_email="malyushkinr@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "jupyter",
        "natasha",
        "pandas",
        "psycopg2-binary",
        "sshtunnel",
        "sqlalchemy",
        f"pandas=={PANDAS_VER}",
    ],
)
