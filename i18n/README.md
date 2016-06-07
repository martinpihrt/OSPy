I18N language localisation
====

For translation to other language opening file: ospy_messages.pot in Poedit editor  
https://poedit.net/ and save to your prefered language. Two files (*.mo *.po)  
transfer via email to: martinpihrt@gmail.com for move files  
add to OSPy on my fork on the github.

for generate ospy_messages.pot use: sudo python pygettext.py -a -v -d messages -o i18n/ospy_messages.pot ospy/\*.py ospy/templates/\*.html 
