#!/usr/bin/env python3
"""
Quick start script for local development.
Checks dependencies and provides setup instructions.
"""

import sys
import subprocess
import os


def check_command(command):
    """Check if a command exists."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"✗ {text}")


def print_info(text):
    """Print info message."""
    print(f"→ {text}")


def main():
    """Main function."""
    print_header("智享会员系统 - 快速启动检查")

    # Check Docker
    print_info("检查 Docker...")
    if check_command("docker"):
        print_success("Docker 已安装")
    else:
        print_error("Docker 未安装")
        print("   请访问 https://docs.docker.com/get-docker/ 安装 Docker")
        sys.exit(1)

    # Check Docker Compose
    print_info("检查 Docker Compose...")
    if check_command("docker-compose") or check_command("docker"):
        print_success("Docker Compose 已安装")
    else:
        print_error("Docker Compose 未安装")
        print("   请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose")
        sys.exit(1)

    # Check if .env exists
    print_info("检查环境配置...")
    if os.path.exists(".env"):
        print_success(".env 文件已存在")
    else:
        print_info("创建 .env 文件...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print_success(".env 文件已创建")
        else:
            print_error(".env.example 文件不存在")

    print_header("启动说明")

    print("1. 启动所有服务:")
    print("   cd docker")
    print("   docker compose up -d")
    print()

    print("2. 查看日志:")
    print("   docker compose logs -f app")
    print()

    print("3. 验证 API:")
    print("   bash ../verify_api.sh")
    print()

    print("4. 访问 API 文档:")
    print("   http://localhost:8000/docs")
    print()

    print("5. 停止服务:")
    print("   docker compose down")
    print()

    print_header("默认账户")
    print("管理员:")
    print("  用户名: admin")
    print("  密码: admin123")
    print()
    print("⚠️  生产环境请立即修改默认密码！")
    print()

    print_header("常用命令")
    print("# 查看服务状态")
    print("docker compose ps")
    print()
    print("# 重启服务")
    print("docker compose restart app")
    print()
    print("# 查看数据库")
    print("docker exec -it membership_postgres psql -U membership -d membership_db")
    print()
    print("# 查看 Redis")
    print("docker exec -it membership_redis redis-cli")
    print()
    print("# 清理所有数据（重新开始）")
    print("docker compose down -v")
    print()

    print_success("环境检查完成！")
    print()


if __name__ == "__main__":
    main()
