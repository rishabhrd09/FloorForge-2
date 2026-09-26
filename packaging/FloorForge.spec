# Build only on the target OS. This is a recipe, not a signed installer.
from pathlib import Path
ROOT=Path(SPECPATH).parent
source_data=[(str(ROOT/"web"),"web"),(str(ROOT/"examples/demo"),"examples/demo"),(str(ROOT/"floorforge"),"floorforge"),(str(ROOT/"licenses"),"licenses"),(str(ROOT/"LICENSE"),".")]
a=Analysis([str(ROOT/"desktop.py")],pathex=[str(ROOT)],binaries=[],datas=source_data,hiddenimports=["numpy","shapely","trimesh","ezdxf","reportlab","PIL","scipy","networkx","tkinter"],hookspath=[],hooksconfig={},runtime_hooks=[],excludes=["pytest","playwright"],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name="FloorForge",debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,disable_windowed_traceback=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name="FloorForge")
import sys
if sys.platform=="darwin":
 app=BUNDLE(coll,name="FloorForge.app",bundle_identifier="local.floorforge.studio",info_plist={"CFBundleShortVersionString":"0.2.0","NSHighResolutionCapable":True})
