from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-dotenv==1.0.0',
        'pyotp==2.9.0',
        'requests==2.31.0',
        'smartapi-python==1.3.0',
        'python-dateutil==2.8.2',
        'pandas==2.2.1',
        'numpy==1.26.4',
        'logzero==1.7.0',
        'websocket-client==1.8.0'
    ]
) 