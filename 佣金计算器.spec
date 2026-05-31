# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\commission\\gui\\launch.py'],
    pathex=[],
    binaries=[],
    datas=[('assets\\app.ico', 'assets')],
    hiddenimports=['commission', 'commission.config', 'commission.calculator', 'commission.feishu', 'commission.gui', 'commission.gui.app', 'commission.gui.resources', 'commission.gui.styles', 'commission.gui.wizard', 'commission.gui.steps', 'commission.gui.steps.step_type', 'commission.gui.steps.step_payment', 'commission.gui.steps.step_roles', 'commission.gui.steps.step_split', 'commission.gui.steps.step_result'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='佣金计算器',
    icon='assets\\app.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
