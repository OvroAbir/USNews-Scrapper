from distutils.core import setup

setup(
    name = 'usnews-scrapper',
    packages = ['usnews-scrapper'],
    version = '0.1',
    license='MIT',
    description = 'Collects Grad School data from https://www.usnews.com and gives output in a .xls file.',
    author = 'Joy Ghosh',
    author_email = 'joyghosh826@gmail.com',
    url = 'https://www.ijoyghosh.com',
    download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
    keywords = ['scraper', 'usnews', 'graduate', 'grad', 'school', 'university', 'crawler'],
    install_requires=[
        'requests==2.22.0',
        'tablib==0.13.0',
        'tqdm==4.32.1',
        'urllib3==1.25.2'
        ],
  classifiers=[
      'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
      'Intended Audience :: Developers',
      'Topic :: Software Development :: Build Tools',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: 3.7',
      ],
)