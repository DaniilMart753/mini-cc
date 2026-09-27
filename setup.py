"""
Установка пакета mini-cc.
Позволяет поставить компилятор как команду:
    pip install -e .
    mini-cc scan --input examples/hello.src
"""

from setuptools import setup, find_packages


setup(
    name="mini-cc",
    version="0.1.0",
    description="Учебный компилятор для упрощённого C-like языка",
    author="Даниил Мартынов",
    python_requires=">=3.8",
    packages=find_packages(include=["src", "src.*"]),
    py_modules=["cli"],
    entry_points={
        "console_scripts": [
            "mini-cc=cli:main",
        ],
    },
)