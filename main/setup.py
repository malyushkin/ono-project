import setuptools

PANDAS_VER = "2.1.1"
PULLENTI_CLIENT_VER = "0.6.0"

setuptools.setup(
    name="Pullenti ONO Client",
    version="0.1",
    author="Roman Maliushkin",
    author_email="malyushkinr@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "jupyter",
        "psycopg2",
        f"pandas=={PANDAS_VER}",
        f"pullenti-client=={PULLENTI_CLIENT_VER}",
    ],
)
