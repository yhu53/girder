System Prerequisites
====================

The following software packages are required to be installed on your system:

* `Python 2.7 or 3.4+ <https://www.python.org>`_
* `pip <https://pypi.python.org/pypi/pi>`_
* `MongoDB 2.6+ <http://www.mongodb.org/>`_
* `Node.js 6.5+ <http://nodejs.org/>`_
* `curl <http://curl.haxx.se/>`_
* `zlib <http://www.zlib.net/>`_
* `libjpeg <http://libjpeg.sourceforge.net/>`_

Additionally, in order to send out emails to users, Girder will need to be able
to communicate with an SMTP server. Proper installation and configuration of
an SMTP server on your system is beyond the scope of these docs, but we
recommend setting up `Postfix <http://www.postfix.org/documentation.html>`_.


Initial Setup
-------------

.. tabs::
   .. group-tab:: Ubuntu 16.04

      To install system package prerequisites, run the command:

      .. code-block:: bash

         sudo apt-get install -y curl build-essential git libffi-dev make python-dev python-pip libssl-dev libjpeg-dev zlib1g-dev

   .. group-tab:: Ubuntu 14.04

      To install system package prerequisites, run the command:

      .. code-block:: bash

         sudo apt-get install -y curl build-essential git libffi-dev make python-dev python-pip libssl-dev libjpeg-dev zlib1g-dev

   .. group-tab:: RHEL (CentOS) 7

      Enable the `Extra Packages for Enterprise Linux <https://fedoraproject.org/wiki/EPEL>`_ YUM
      repository:

      .. code-block:: bash

         sudo yum -y install epel-release

      To install system package prerequisites, run the command:

      .. code-block:: bash

         sudo yum install curl gcc-c++ make git libffi-devel make python-devel python-pip openssl-devel libjpeg-turbo-devel zlib-devel

   .. group-tab:: macOS

      Install `Homebrew <http://brew.sh/>`_.

Python
------
.. note:: We perform continuous integration testing using Python 2.7 and Python 3.4.
   The system *should* work on other versions of Python 3 as well, but we do not
   verify that support in our automated testing at this time, so use at your own
   risk.

.. warning:: Some Girder plugins do not support Python 3 at this time due to
   third party library dependencies. Namely, the HDFS Assetstore plugin and the
   Metadata Extractor plugin will only be available in a Python 2.7 environment.

.. tabs::
   .. group-tab:: Ubuntu 16.04

      TODO

   .. group-tab:: Ubuntu 14.04

      TODO

   .. group-tab:: RHEL (CentOS) 7

      TODO

   .. group-tab:: macOS

      To install all the prerequisites at once just use:

      .. code-block:: bash

         brew install python

      .. note:: OS X ships with Python in ``/usr/bin``, so you might need to change your
         PATH or explicitly run ``/usr/local/bin/python`` when invoking the server so
         that you use the version with the correct site packages installed.

MongoDB
-------
Girder can connect to any instance of `MongoDB <https://www.mongodb.com/>`_ v3.0 or later, running
on any machine. If MongoDB is going to be installed locally for development or a simple deployment,
it is recommended that the latest release (v3.4) be installed.

.. tabs::
   .. group-tab:: Ubuntu 16.04

      To install, run the commands:

      .. code-block:: bash

         sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
         echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
         sudo apt-get update
         sudo apt-get install -y mongodb-org-server mongodb-org-shell

      MongoDB server will register itself as a systemd service (called ``mongod``). To start it
      immediately and on every reboot, run the commands:

      .. code-block:: bash

         sudo systemctl start mongod
         sudo systemctl enable mongod

   .. group-tab:: Ubuntu 14.04

      To install, run the commands:

      .. code-block:: bash

         sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
         echo "deb [ arch=amd64 ] http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
         sudo apt-get update
         sudo apt-get install -y mongodb-org-server mongodb-org-shell

      MongoDB server will register itself as an Upstart service (called ``mongod``), and will
      automatically start immediately and on every reboot.

   .. group-tab:: RHEL (CentOS) 7

      To install, create a file at ``/etc/yum.repos.d/mongodb-org-3.4.repo``, with:

      .. code-block:: cfg

         [mongodb-org-3.4]
         name=MongoDB Repository
         baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.4/x86_64/
         gpgcheck=1
         enabled=1
         gpgkey=https://www.mongodb.org/static/pgp/server-3.4.asc

      then run the command:

      .. code-block:: bash

         sudo yum -y install mongodb-org-server mongodb-org-shell

      MongoDB server will register itself as a systemd service (called ``mongod``), and will
      autoamtically start on every reboot. To start it immediately, run the command:

      .. code-block:: bash

         sudo systemctl start mongod

   .. group-tab:: macOS

      To install, run the command:

      .. code-block:: bash

         brew install mongodb

      TODO: does this auto-start?

Node.js
-------
Girder requires `Node.js <https://nodejs.org/>`_ v6.5 or later to build its web client components.
To ensure stability, it is recommended that the
`Active LTS release <https://github.com/nodejs/LTS#lts-schedule1>`_ (v6.x) be installed.

.. tabs::
   .. group-tab:: Ubuntu 16.04

      To install, run the commands:

      .. code-block:: bash

         curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
         sudo apt-get install -y nodejs

   .. group-tab:: Ubuntu 14.04

      To install, run the commands:

      .. code-block:: bash

         curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
         sudo apt-get install -y nodejs

   .. group-tab:: RHEL (CentOS) 7

      To install, run the commands:

      .. code-block:: bash

         curl --silent --location https://rpm.nodesource.com/setup_6.x | sudo bash -
         sudo yum -y install nodejs

   .. group-tab:: macOS

      To install, run the command:

      .. code-block:: bash

         brew install node

npm
---
Girder requires `npm <https://docs.npmjs.com/>`_ to install web client packages. While Node.js v6
will install npm v3.10 by default, is it **strongly recommended that npm v5.3 or later be
installed**.

To upgrade to the latest npm on all platforms, either:

- `Fix npm's global permissions <https://docs.npmjs.com/getting-started/fixing-npm-permissions>`_,
  then run the command :

  .. code-block:: bash

     npm install -g npm

- Or just run the command:

  .. code-block:: bash

     sudo npm install -g npm
