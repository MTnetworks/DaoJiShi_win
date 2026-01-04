#!/bin/bash

# 错误处理：任何命令失败则退出
set -e

echo "开始构建 DaoJiShi DEB 包..."

# 0. 环境准备
# 确保在脚本所在目录运行
cd "$(dirname "$0")"
PROJECT_ROOT=".."

# 1. 清理旧构建
echo "清理旧构建文件..."
rm -rf build dist deb_package *.deb

# 2. 安装依赖
echo "检查并安装依赖..."
pip3 install -r $PROJECT_ROOT/requirements.txt pyinstaller

# 3. 使用 PyInstaller 打包
echo "运行 PyInstaller..."
# 注意：Linux 下 add-data 使用冒号 : 分隔
pyinstaller --clean --noconfirm --windowed --name=DaoJiShi \
    --add-data="$PROJECT_ROOT/app/source:app/source" \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --hidden-import=keyboard \
    $PROJECT_ROOT/app/main.py

# 4. 准备 DEB 包结构
echo "准备 DEB 目录结构..."
mkdir -p deb_package/DEBIAN
mkdir -p deb_package/opt/daojishi
mkdir -p deb_package/usr/share/applications

# 5. 复制文件
echo "复制文件..."
# 复制控制文件
cp control deb_package/DEBIAN/
# 赋予 control 文件执行权限（通常不需要，但为了保险）
chmod 755 deb_package/DEBIAN/control

# 复制编译好的程序
cp -r dist/DaoJiShi/* deb_package/opt/daojishi/

# 复制 desktop 文件
cp daojishi.desktop deb_package/usr/share/applications/

# 处理图标
# 尝试查找 ico 文件并作为图标（虽然 Linux 推荐 png）
if [ -f "$PROJECT_ROOT/app/source/time.ico" ]; then
    cp "$PROJECT_ROOT/app/source/time.ico" deb_package/opt/daojishi/icon.ico
    # 如果系统有 ImageMagick 的 convert 工具，尝试转换为 png
    if command -v convert >/dev/null 2>&1; then
        echo "正在将 ico 转换为 png..."
        convert deb_package/opt/daojishi/icon.ico deb_package/opt/daojishi/icon.png
    else
        echo "未找到 convert 工具，直接使用 ico 文件作为图标源（可能不显示）。"
        echo "建议安装 imagemagick: sudo apt install imagemagick"
        # 简单地重命名，虽然格式不对，但某些桌面环境可能兼容，或者直接复制一份
        cp deb_package/opt/daojishi/icon.ico deb_package/opt/daojishi/icon.png
    fi
else
    echo "警告：未找到图标文件！"
fi

# 赋予可执行权限
chmod +x deb_package/opt/daojishi/DaoJiShi

# 6. 构建 DEB 包
echo "构建 .deb 包..."
# 获取架构信息 (默认 amd64，如果是 arm64 如 UOS 某些版本，可能需要调整)
ARCH=$(dpkg --print-architecture)
VERSION=$(grep "Version:" control | cut -d' ' -f2)
DEB_NAME="daojishi_${VERSION}_${ARCH}.deb"

# 更新 control 文件中的架构
sed -i "s/Architecture: .*/Architecture: $ARCH/" deb_package/DEBIAN/control

dpkg-deb --build deb_package "$DEB_NAME"

echo "========================================"
echo "打包完成！"
echo "文件位置: $(pwd)/$DEB_NAME"
echo "安装命令: sudo dpkg -i $DEB_NAME"
echo "========================================"
