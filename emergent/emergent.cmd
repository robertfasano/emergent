if "%~2"=="" (goto blank) else goto arg

:blank
ipython -i main.py -- %1
goto done

:arg
ipython -i main.py -- %1 --addr %2
goto done

:done
