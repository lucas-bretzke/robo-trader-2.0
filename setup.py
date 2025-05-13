from setuptools import setup, find_packages

setup(
    name="robo-trader",
    version="2.0",
    packages=find_packages(),
    install_requires=[
        "iqoptionapi==7.1.1",
        "fastapi==0.100.0",
        "uvicorn==0.23.1",
        "pandas==2.0.3",
        "numpy==1.24.4",
        "websockets==11.0.3",
        "python-multipart==0.0.6",
        "aiofiles==23.1.0",
    ],
    python_requires=">=3.8,<3.12",
)
