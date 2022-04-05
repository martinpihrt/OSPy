Python 2
Copy ospy.service to etc/systemd/system:

```bash
sudo cp OSPy/service/ospy.service /etc/systemd/system
```

Ran:
```bash
systemctl enable ospy.service
```

Started ospy:
```bash
systemctl start ospy
```

Python 3
Copy ospy3.service to etc/systemd/system:

```bash
sudo cp OSPy/service/ospy3.service /etc/systemd/system
```

Ran:
```bash
systemctl enable ospy3.service
```

Started ospy:
```bash
systemctl start ospy
```

