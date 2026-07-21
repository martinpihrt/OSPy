The clean-installation script is the preferred way to install the service. It reads `ospy.service`, replaces `{{OSPY_DIR}}` and `{{PYTHON}}` with verified absolute paths, installs the rendered file, reloads systemd and verifies that OSPy starts.

For a manual installation, render both placeholders before copying the file. Do not copy the unmodified template into `/etc/systemd/system`, because systemd cannot resolve the placeholder paths.

Example for OSPy installed in `/opt/OSPy`:

```bash
sed -e 's|{{OSPY_DIR}}|/opt/OSPy|g' \
    -e 's|{{PYTHON}}|/usr/bin/python3|g' \
    /opt/OSPy/service/ospy.service | sudo tee /etc/systemd/system/ospy.service >/dev/null
sudo systemctl daemon-reload
```

Enable and start OSPy:
```bash
sudo systemctl enable --now ospy.service
sudo systemctl is-active ospy.service
```

Emergency administrator login recovery
----

If the administrator password or second factor is unavailable, stop OSPy or run the recovery from another trusted local shell in the OSPy directory:

```bash
sudo service ospy stop
sudo python3 back_door.py
sudo service ospy start
```

Stop the service first so the settings database is closed, then confirm recovery by typing `RESET`. The script generates a new recovery password for `admin`, disables two-factor authentication, clears its secret and backup codes, revokes remembered browser logins, and changes the session secret so active web sessions become invalid after OSPy starts again. It does not delete irrigation settings, programs, plug-ins, or logs. Log in with the displayed password and change it immediately. Full details are in [`ospy/docs/Clean_installation.md`](../ospy/docs/Clean_installation.md).

Hardware relay board test before starting OSPy
----

Use `relay_test.py` to test the relay board and GPIO wiring before the first OSPy start or while diagnosing hardware. The script switches all eight shift-register relays and the additional main relay on and off together every 1.5 seconds.

**Warning:** Disconnect pumps, valves, contactors, and other equipment that must not start. Every relay is energized during the test, and the OSPy service must not use the GPIO pins at the same time.

```bash
sudo service ospy stop
sudo python3 relay_test.py
```

Stop the test with `Ctrl+C`. The script switches the outputs off and calls GPIO cleanup before exiting. Then start OSPy:

```bash
sudo service ospy start
```

