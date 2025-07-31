
# AGENTY Console Application Functions
agenty() { cd '/home/marcin/Dokumenty/PROJEKT/AGENTY' && ./start_agenty_console.sh; }
agenty-test() { cd '/home/marcin/Dokumenty/PROJEKT/AGENTY' && python test_console.py; }
agenty-console() { cd '/home/marcin/Dokumenty/PROJEKT/AGENTY' && python console_agenty_enhanced.py; }
agenty-simple() { cd '/home/marcin/Dokumenty/PROJEKT/AGENTY' && python console_agenty.py; }
agenty-backend() { cd '/home/marcin/Dokumenty/PROJEKT/AGENTY/agenty/backend' && python main.py; }

# Również aliasy dla kompatybilności
alias agenty='cd /home/marcin/Dokumenty/PROJEKT/AGENTY && ./start_agenty_console.sh' 
alias agenty-test='cd /home/marcin/Dokumenty/PROJEKT/AGENTY && python test_console.py'
alias agenty-console='cd /home/marcin/Dokumenty/PROJEKT/AGENTY && python console_agenty_enhanced.py'
alias agenty-simple='cd /home/marcin/Dokumenty/PROJEKT/AGENTY && python console_agenty.py'
alias agenty-backend='cd /home/marcin/Dokumenty/PROJEKT/AGENTY/agenty/backend && python main.py'

