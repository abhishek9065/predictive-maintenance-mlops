from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="predictive-maintenance-mlops",
    version="1.0.0",
    author="MLOps Team",
    author_email="mlops@example.com",
    description="A comprehensive MLOps solution for predictive maintenance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/predictive-maintenance-mlops",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "train-model=training.train:main",
            "deploy-api=deployment.api:main",
            "monitor-model=monitoring.performance_monitor:main",
        ],
    },
)
