"""
一键构建脚本（跨平台）
Windows  → 绿色版 zip + 安装版 Setup.exe（需要 Inno Setup 6）
macOS    → .app 压缩包 zip
Linux    → tar.gz 压缩包
"""
import os
import sys
import json
import shutil
import subprocess
import zipfile
import tarfile

# 强制 stdout/stderr 使用 UTF-8，避免 Windows CI 环境 cp1252 编码报错
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

IS_WINDOWS = sys.platform == 'win32'
IS_MACOS   = sys.platform == 'darwin'
IS_LINUX   = sys.platform.startswith('linux')

ROOT      = os.path.dirname(os.path.abspath(__file__))
SPEC      = os.path.join(ROOT, "video_bd.spec")
DIST_BASE = os.path.join(ROOT, "dist")
RELEASE   = os.path.join(DIST_BASE, "release")
ISS       = os.path.join(ROOT, "installer.iss")

# macOS 产物是 .app bundle；其余平台是同名目录
if IS_MACOS:
    DIST_DIR = os.path.join(DIST_BASE, "build", "video_bd.app")
else:
    DIST_DIR = os.path.join(DIST_BASE, "build", "video_bd")

ISCC_CANDIDATES = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]


def get_version():
    config = os.path.join(ROOT, "src", "config", "config.json")
    with open(config, encoding="utf-8") as f:
        return json.load(f)["software_version"]


def step(msg):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print('='*50)


def find_iscc():
    for path in ISCC_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


# ── 1. 清理旧产物 ─────────────────────────────────────────────
step("清理旧构建产物")
for p in [os.path.join(ROOT, "build"), DIST_BASE]:
    if os.path.exists(p):
        shutil.rmtree(p)
        print(f"  已删除: {os.path.relpath(p, ROOT)}/")
os.makedirs(RELEASE, exist_ok=True)


# ── 2. PyInstaller 打包 ──────────────────────────────────────
step("PyInstaller 打包")
result = subprocess.run(
    [sys.executable, "-m", "PyInstaller", "--noconfirm",
     "--distpath", os.path.join(DIST_BASE, "build"),
     "--workpath", os.path.join(DIST_BASE, "work"),
     SPEC],
    cwd=ROOT
)
if result.returncode != 0:
    print("❌ PyInstaller 打包失败，终止构建")
    sys.exit(1)
print("✅ PyInstaller 打包完成")

version = get_version()


# ── 3. 打包产物 ───────────────────────────────────────────────
if IS_WINDOWS:
    # ── Windows：绿色版 zip ──
    step("生成绿色版 zip（Windows）")
    zip_name = f"video_bd_v{version}_windows_portable.zip"
    zip_path = os.path.join(RELEASE, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(DIST_DIR):
            dirs[:] = [d for d in dirs if d not in ["__pycache__"]]
            for file in files:
                abs_path = os.path.join(root, file)
                arc_path = os.path.join(
                    f"video_bd_v{version}",
                    os.path.relpath(abs_path, DIST_DIR)
                )
                zf.write(abs_path, arc_path)

    print(f"✅ 绿色版已生成: release/{zip_name}")

    # ── Windows：Inno Setup 安装包 ──
    step("编译安装包（Inno Setup）")
    iscc = find_iscc()
    if not iscc:
        print("⚠️  未找到 Inno Setup，跳过安装包生成")
        print("   请安装 Inno Setup 6：https://jrsoftware.org/isdl.php")
    else:
        result = subprocess.run([iscc, f"/O{RELEASE}", ISS], cwd=ROOT)
        if result.returncode != 0:
            print("❌ 安装包编译失败")
            sys.exit(1)
        print(f"✅ 安装包已生成: release/video_bd_Setup_v{version}.exe")

elif IS_MACOS:
    # ── macOS：zip ──
    step("生成 macOS zip")
    zip_name = f"video_bd_v{version}_macos.zip"
    zip_path = os.path.join(RELEASE, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(DIST_DIR):
            dirs[:] = [d for d in dirs if d not in ["__pycache__"]]
            for file in files:
                abs_path = os.path.join(root, file)
                arc_path = os.path.relpath(abs_path, os.path.dirname(DIST_DIR))
                zf.write(abs_path, arc_path)

    print(f"✅ macOS zip 已生成: release/{zip_name}")

    # ── macOS：dmg ──
    step("生成 macOS dmg")
    dmg_name = f"video_bd_v{version}_macos.dmg"
    dmg_path = os.path.join(RELEASE, dmg_name)
    result = subprocess.run([
        'hdiutil', 'create',
        '-volname', 'video_bd',
        '-srcfolder', DIST_DIR,
        '-ov', '-format', 'UDZO',
        dmg_path
    ], cwd=ROOT)
    if result.returncode != 0:
        print("⚠️  dmg 生成失败，跳过")
    else:
        print(f"✅ macOS dmg 已生成: release/{dmg_name}")

else:
    # ── Linux：tar.gz ──
    step("生成 Linux tar.gz")
    tar_name = f"video_bd_v{version}_linux.tar.gz"
    tar_path = os.path.join(RELEASE, tar_name)

    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(DIST_DIR, arcname=f"video_bd_v{version}")

    print(f"✅ Linux 包已生成: release/{tar_name}")


# ── 4. 清理临时目录 ───────────────────────────────────────────
step("清理临时目录")
work_dir = os.path.join(DIST_BASE, "work")
if os.path.exists(work_dir):
    shutil.rmtree(work_dir)
    print("  已删除: dist/work/")


# ── 完成 ──────────────────────────────────────────────────────
step("构建完成")
print(f"\n📦 产物目录: dist/release/")
for f in sorted(os.listdir(RELEASE)):
    size = os.path.getsize(os.path.join(RELEASE, f)) / 1024 / 1024
    print(f"   {f}  ({size:.1f} MB)")
