Network Metrix
github.com/ms83
v. 2016-09-30


# INSTALLATION

Make sure `pip` is installed and run:

```
make install
make test
```

# CONFIGURATION

config.xml --- server and clients configuration
Source/client.py --- secret key for client-server encryption


# RUNNING
```
$ ./server <command>
$ ./server --help
```

# TODO

- Windows event log (check client.py:29)
- TLS and SSL in SMTP (check config.xml and smtp.py)
- SSH timeouts
- Test on Windows

