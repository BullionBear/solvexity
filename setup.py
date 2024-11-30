from setuptools import setup, find_packages

setup(
    name='solvexity',
    version='0.1.0',
    author='Yi Te',
    author_email='yite@lynxlinkage.com',  # Replace with your email
    description="""
        solvexity is a crypto trading bot designed to help traders execute 
        disciplined live trading while leveraging their financial and mathematical 
        expertise. It provides a modular and extensible framework for analyzing, 
        diagnosing, and improving trading strategies.
        """,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/BullionBear/solvexity',  # Replace with your project's URL
    packages=['solvexity'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    install_requires=open('requirements.txt').readlines(),  # Assumes dependencies are in requirements.txt
)