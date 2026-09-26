"""Native windowed launcher for PyInstaller builds. No shell, no terminal."""
from pathlib import Path
import threading,webbrowser,sys
import tkinter as tk
from tkinter import messagebox

def main():
 try:
  from floorforge.server import make_server
  server=make_server(Path.home()/".floorforge")
 except Exception as exc:
  root=tk.Tk();root.withdraw();messagebox.showerror("FloorForge could not start",str(exc));return 1
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 url=f"http://127.0.0.1:{server.server_port}/"
 root=tk.Tk();root.title("FloorForge");root.geometry("460x265");root.resizable(False,False)
 root.configure(bg="#f3f1e8")
 tk.Label(root,text="F L O O R F O R G E",font=("Helvetica",19,"bold"),bg="#f3f1e8",fg="#233a2b").pack(pady=(30,14))
 tk.Label(root,text="Your private studio is running on this laptop.\nNo account. No telemetry. Preliminary design only.",bg="#f3f1e8",fg="#52634f",justify="center").pack()
 tk.Button(root,text="Open the studio",command=lambda:webbrowser.open(url),padx=25,pady=8).pack(pady=17)
 closing=False
 def close():
  nonlocal closing
  if closing:return
  closing=True
  server.state.ai.clear();server.shutdown();server.server_close();server.state.pool.shutdown(wait=False,cancel_futures=True);root.destroy()
 tk.Button(root,text="Stop and quit",command=close).pack()
 root.protocol("WM_DELETE_WINDOW",close);root.after(700,lambda:webbrowser.open(url));root.mainloop();return 0
if __name__=="__main__":raise SystemExit(main())
