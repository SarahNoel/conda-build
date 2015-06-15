# (c) Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# conda is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.

import os
import sys
from os.path import isdir, join

try:
    from Crypto.PublicKey import RSA
    from Crypto import Random
except ImportError:
    sys.exit("""\
Error: could not import Crypto (required for "conda sign").
    Run the following command:

    $ conda install -n root pycrypto
""")

from conda.signature import (KEYS_DIR, hash_file, sig2ascii,
                             verify, SignatureError)



def keygen(name):
    print("Generating public/private key pair...")
    random_generator = Random.new().read
    key = RSA.generate(1024, random_generator)

    if not isdir(KEYS_DIR):
        os.makedirs(KEYS_DIR)

    path = join(KEYS_DIR, name)
    print("Storing private key: %s" % path)
    with open(path, 'wb') as fo:
        fo.write(key.exportKey())
        fo.write(b'\n')

    path = join(KEYS_DIR, '%s.pub' % name)
    print("Storing public key : %s" % path)
    with open(path, 'wb') as fo:
        fo.write(key.publickey().exportKey())
        fo.write(b'\n')


def get_default_keyname():
    if isdir(KEYS_DIR):
        for fn in os.listdir(KEYS_DIR):
            if not fn.endswith('.pub'):
                return fn
    return None


def sign(path, key):
    return sig2ascii(key.sign(hash_file(path), '')[0])


def main():
    from optparse import OptionParser

    p = OptionParser(
        usage="usage: %prog [option] [FILE ...]",
        description="tool for signing conda packages")

    p.add_option('-k', '--keygen',
                 action="store",
                 help="generate a public-private "
                      "key pair ~/.conda/keys/<NAME>(.pub)",
                 metavar="NAME")

    p.add_option('-v', '--verify',
                 action="store_true",
                 help="verify FILE(s)")

    opts, args = p.parse_args()

    if opts.keygen:
        if args:
            p.error('no arguments expected for --keygen')
        keygen(opts.keygen)
        return

    if opts.verify:
        for path in args:
            try:
                disp = 'VALID' if verify(path) else 'INVALID'
            except SignatureError as e:
                disp = 'ERROR: %s' % e
            print('%-40s %s' % (path, disp))
        return

    key_name = get_default_keyname()
    if key_name is None:
        sys.exit("Error: no private key found in %s" % KEYS_DIR)
    print("Using private key '%s' for signing." % key_name)
    key = RSA.importKey(open(join(KEYS_DIR, key_name)).read())
    for path in args:
        print('signing: %s' % path)
        with open('%s.sig' % path, 'w') as fo:
            fo.write('%s ' % key_name)
            fo.write(sign(path, key))
            fo.write('\n')


if __name__ == '__main__':
    main()
