# HTTPS connections
## This directory is used to hold SSL cirtificate and key.

If "Use Own HTTPS access" is selected in OSPy settings, file: fullchain.pem and privkey.pem must You insert to folder ssl in OSPy location. Warning: OSPy must be next restarted.

For manual generating certificate example:

```bash
cd ssl  
```

```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem  
```
