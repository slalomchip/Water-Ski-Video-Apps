# -*- mode: python ; coding: utf-8 -*-

version = 'VTMv121'
fileName = version + '.py'

block_cipher = None

a = Analysis([fileName],
             pathex=['c:\\Users\\slalo\\Documents\\VTMBuild'],
             binaries=[],
             datas=[('CustomCombo.py','.'),
					('VTMConfig.py','.'),
					('VTMLayout.py','.'),
					('WSC.py','.'),
					('WSCDialog.py','.'),
					('ffmpeg.exe','.'),
                    ('VTMIcon.ico','.'),
                    ('VTMIconSmall.ico','.'),
					('WSCConnected64.png','.'),
					('WSCDisconnected64.png','.'),
                    ('VTMLicense.txt','.'),
					('VTM Release Notes.txt','.'),
                    ('VTMManual.htm','.'),
                    ('VTMManual_files','VTMManual_files'),
                    ('opencv_videoio_ffmpeg430_64.dll','.'),
					('pymf.pyd','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name=version,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
		  icon='VTMIcon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name=version)
