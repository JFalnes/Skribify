from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Skribify",
    version="0.1.8",
    author="JFalnes",
    author_email="post@falnes.dev",
    description="A transcription and summarization tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jfalnes/Skribify",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
    install_requires=[
        'openai',
        'python-dotenv',
        'pydub',
    ],
)
