## For enable SSL access in options (for HTTPS connections)
1. Execute: sudo apt-get install openssl
2. Execute: sudo openssl version
3. Execute: sudo cd OSPy/ssl
4. Execute: sudo openssl genrsa -des3 -out server.key 1024
5. Execute: sudo openssl req -new -key server.key -out server.csr
6. Execute: sudo openssl x509 -req -days 365123 -in server.csr -signkey server.key -out server.crt
7. Execute: sudo openssl rsa -in server.key -out server.key
