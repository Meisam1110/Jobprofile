' Opens Job Profile Management in the browser, starting the server first if needed.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)

port = "8000"
cfg = dir & "\config.bat"
If fso.FileExists(cfg) Then
  Set re = New RegExp
  re.Pattern = "JP_PORT=(\d+)"
  Set f = fso.OpenTextFile(cfg, 1)
  Do Until f.AtEndOfStream
    line = f.ReadLine
    If re.Test(line) Then port = re.Execute(line)(0).SubMatches(0)
  Loop
  f.Close
End If

url = "http://localhost:" & port

Function IsUp(u)
  IsUp = False
  On Error Resume Next
  Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  h.setTimeouts 1000, 1000, 1000, 1000
  h.open "GET", u, False
  h.send
  If Err.Number = 0 Then
    If h.status = 200 Then IsUp = True
  End If
  On Error GoTo 0
End Function

If Not IsUp(url & "/api/health") Then
  sh.Run "wscript.exe """ & dir & "\run-hidden.vbs""", 0, False
  For i = 1 To 40
    WScript.Sleep 1000
    If IsUp(url & "/api/health") Then Exit For
  Next
End If

sh.Run url
