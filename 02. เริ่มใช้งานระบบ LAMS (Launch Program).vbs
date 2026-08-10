Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")
strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strCmd = Chr(34) & strDir & "\run_background.bat" & Chr(34)
objShell.Run strCmd, 0
Set objShell = Nothing
Set objFSO = Nothing
