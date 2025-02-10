from setuptools import setup, find_packages

setup(
    name="zero_sum_eval",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        "dspy-ai==2.5.41",
        "pyyaml>=6.0",
        "anthropic>=0.3.0",
        "tabulate>=0.9.0",
        "jsonlines>=3.1.0",
        "docker>=6.0.0",
        "random-word>=1.0.11",
        
        # Game-specific dependencies
        "chess>=1.9.0",  # For chess game
        "stockfish>=3.28.0",  # For chess evaluation
        "datasets>=2.12.0",  # For chess dataset loading
        
        # Testing dependencies
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-runner>=6.0.0"
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-runner>=6.0.0'
        ]
    },
    author="Haidar Khan",
    author_email="haidark@gmail.com",
    description="A framework for evaluating LLMs using zero-sum multiplayer simulations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/haidark/ZeroSumEval/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    python_requires=">=3.8",  # Updated based on f-strings and type hints usage
    entry_points={
        'console_scripts': [
            'zse=zero_sum_eval.main:cli_run',
        ],
    },
)