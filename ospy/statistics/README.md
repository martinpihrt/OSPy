PHP script ipbot.php Readme 
====

This code "ipbot.php" iterats through $_SERVER and finds the most reliable IP address to return. The only address you can really trust is REMOTE_ADDR, because it is the source IP of the TCP connection and cant be changed my spoofing/changing an http header. While it is technically possible to bidirectionally spoof ID Addressed at the Border Gate way level, but you would have to have control over an ISP to do so. Return example: https://pihrt.com/ipbot.php -> return 191.112.180.131.


