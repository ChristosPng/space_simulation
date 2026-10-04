@echo off
echo Compiling C++ physics engine...
g++ -O3 -shared -o physics.dll physics.cpp

echo Packaging executable with PyInstaller...
pyinstaller --noconsole --onefile --icon="icon.ico" --name="orbital_sim" --add-data "sounds;sounds" --add-binary "physics.dll;." main.py

echo Cleaning up temporary build files...
rmdir /s /q build
del orbital_sim.spec

echo.
echo Build complete! Your game is in the "dist" folder.
pause