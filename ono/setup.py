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
        "psycopg2-binary",
        f"pandas=={PANDAS_VER}",
    ],
)
