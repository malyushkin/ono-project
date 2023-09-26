import setuptools

PULLENTI_CLIENT_VER = "0.6.0"

setuptools.setup(
    name="Pullenti ONO Client",
    version="0.1",
    author="Roman Maliushkin",
    author_email="malyushkinr@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=[
        f"pullenti-client=={PULLENTI_CLIENT_VER}"
    ],
)
