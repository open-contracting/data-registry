Cloudflare Turnstile clearances
===============================

Some publications are protected by `Cloudflare Turnstile <https://www.cloudflare.com/products/turnstile/>`__. Our approach is to solve the challenge manually and reuse the ``cf_clearance`` cookie (which can last a year) in Scrapy crawls.

Solve the challenge from the server's IP
----------------------------------------

.. note::

   You must solve the challenge using a browser and operating system for which ``curl_cffi`` has a `fingerprint <https://curl-impersonate.readthedocs.io/en/latest/fingerprints.html>`__. The browser version need not match.

The clearance is bound to the browser and IP that solved the challenge. So, you need to proxy through the server then solve the challenge.

#. Open a SOCKS proxy through the server that runs Scrapyd:

   .. code-block:: bash

      ssh -D 1080 ocp29.open-contracting.org

#. Launch a Chrome instance using this proxy server under an isolated profile. On macOS:

   .. code-block:: bash

      /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --proxy-server="socks5://localhost:1080" \
        --user-data-dir="/tmp/cf-solve" \
        --no-first-run \
        https://www.cloudflare.com/cdn-cgi/trace

#. On the trace page, confirm the ``ip=`` value is the **server's** IP, not yours.

#. In the same window, open https://opentender.eu/download (or the relevant source) and solve the "Verify you are human" challenge. Then, collect:

   -  **Cookie**: DevTools > Application > Cookies > *the site's domain* > copy the ``cf_clearance`` value
   -  **User-Agent**: DevTools > Console > run ``navigator.userAgent`` > copy the User-Agent value

.. seealso:: `Supported impersonate browsers <https://github.com/lexiforest/curl_cffi#supported-impersonate-browsers>`__

.. _cloudflare-bundle:

Create or update the settings bundle
------------------------------------

In the Django admin under `Scrapy settings bundles <https://data.open-contracting.org/admin/data_registry/settingsbundle/>`__, add or edit a bundle named after the source with these settings:

.. list-table::
   :header-rows: 1

   * - Key
     - Value
   * - CF_CLEARANCE
     - The ``cf_clearance`` value
   * - CF_USER_AGENT
     - The ``User-Agent`` value
   * - CURL_IMPERSONATE
     - The closest `target name <https://curl-impersonate.readthedocs.io/en/latest/fingerprints.html>`__ not newer than ``Chrome/<version>`` in ``User-Agent``
   * - CURL_IP_VERSION
     - ``4`` or ``6``, matching the IP version of ``ip=`` value

Then, link each relevant publication to the settings bundle.
