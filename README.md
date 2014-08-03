# Random Internet Sampling

This repository holds a script for generating a random sample of the Internet.
Random URLs are generated and tested with HTTP requests, and the ones
which eventually return ```200 OK``` are printed to stdout.

## Setup

Build a virtualenv to run the script with. You will need:

* Python 3.4
* Some kind of distutils/setuptools install.
* Some version of virtualenv

Then run the script with ```./mkenv``` and use ```source env/bin/activate```
to use the virtualenv. After that, you can just run the script.

```
./random_internet.py -h # Display some help, showing more info.
```

### What If I'm Running Windows?

Please stop doing that.

## Contribution

Fork this or eat it or whatever. Have fun.
