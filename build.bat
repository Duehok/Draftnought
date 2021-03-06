pip install pyinstaller
pip install -r requirements.txt
rmdir .\dist /s /q
rmdir .\build /s /q
pyinstaller main.py -F --name="Draftnought"
COPY icon.ico .\dist\icon.ico
COPY "README.md" ".\dist\README.md"
COPY LICENSE .\dist\LICENSE
xcopy /s /i ".\data" ".\dist\data"
rmdir %localappdata%\Draftnought /s /q
.\dist\Draftnought.exe