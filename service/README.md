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

