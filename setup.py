from setuptools import setup, find_packages

setup(
    name="zero_sum_eval",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dspy-ai>=2.5",
        "chess",
        "pyyaml",
        "anthropic",
        "tabulate",
        "jsonlines",
        "docker",
        "random_word"
    ],
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
    ],
    python_requires=">=3.6",
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov'],
)