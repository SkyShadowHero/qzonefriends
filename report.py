# 文件名: report_generator.py
import pandas as pd
import os
from tqdm import tqdm
import platform
import subprocess

# --- 脚本配置 ---
# 结果文件夹的根目录
RESULTS_BASE_DIR = './resource/result/'
# -----------------


def open_file_or_path(path):
    """跨平台打开文件或文件夹"""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin": # macOS
            subprocess.run(["open", path])
        else: # Linux
            subprocess.run(["xdg-open", path])
    except Exception:
        print(f"无法自动打开文件，请手动访问：{path}")


def generate_html_from_excel(excel_path):
    """从包含本地路径的Excel生成HTML报告"""
    print(f"开始处理文件: {excel_path}")

    if not os.path.exists(excel_path):
        print(f"错误：找不到Excel文件！请确保路径正确: {excel_path}")
        return

    base_path = os.path.dirname(excel_path)

    try:
        df = pd.read_excel(excel_path)
        # 检查必要的列是否存在
        required_columns = ['时间', '内容', '本地图片路径', '本地视频路径']
        if not all(col in df.columns for col in required_columns):
            print("错误：Excel文件缺少必要的列。请使用最新版的 main.py 重新生成Excel文件。")
            print(f"需要包含: {', '.join(required_columns)}")
            return
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return

    print(f"成功读取 {len(df)} 条动态。")

    target_uin = os.path.basename(base_path)
    html_content = f"""
    <!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>动态报告 - {target_uin}</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background-color:#f0f2f5;margin:0;padding:20px;}}.container{{max-width:800px;margin:auto;}}h1{{text-align:center;color:#333;}}.post-card{{background-color:#fff;border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.12);}}.post-time{{color:#888;font-size:0.9em;margin-bottom:10px;}}.post-content{{font-size:1.1em;line-height:1.6;white-space:pre-wrap;word-wrap:break-word;}}.media-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:15px;}}.media-grid img,.media-grid video{{width:100%;height:100%;object-fit:cover;border-radius:6px;cursor:pointer;}}</style></head><body><div class="container"><h1>动态报告 - {target_uin}</h1>
    """

    for index, row in tqdm(df.iterrows(), total=len(df), desc="生成HTML卡片"):
        post_time = row['时间']
        content = str(row['内容']).replace('\n', '  ') if pd.notna(row['内容']) else ''
        
        media_html = '<div class="media-grid">'
        
        # 直接从Excel读取本地图片路径
        if pd.notna(row['本地图片路径']):
            local_pic_paths = str(row['本地图片路径']).split(', ')
            for pic_path in local_pic_paths:
                if pic_path: # 确保路径不为空
                    media_html += f'<a href="{pic_path}" target="_blank"><img src="{pic_path}" alt="图片"></a>'
        
        # 直接从Excel读取本地视频路径
        if pd.notna(row['本地视频路径']):
            local_video_path = str(row['本地视频路径'])
            if local_video_path: # 确保路径不为空
                media_html += f'<video controls src="{local_video_path}" preload="metadata"></video>'

        media_html += '</div>'
        
        html_content += f"""<div class="post-card"><div class="post-time">{post_time}</div><div class="post-content">{content}</div>{media_html}</div>"""

    html_content += "</div></body></html>"

    report_path = os.path.join(base_path, 'generated_report.html')
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n报告生成成功！文件已保存至: {report_path}")
        open_file_or_path(report_path)
    except Exception as e:
        print(f"保存HTML文件时出错: {e}")


def main():
    """主函数，扫描并让用户选择"""
    if not os.path.exists(RESULTS_BASE_DIR):
        print(f"错误：找不到结果文件夹 '{RESULTS_BASE_DIR}'。")
        print("请确保脚本与 'resource' 文件夹在同一目录下，并且已经至少成功备份过一个好友。")
        return

    try:
        available_backups = [d for d in os.listdir(RESULTS_BASE_DIR) if os.path.isdir(os.path.join(RESULTS_BASE_DIR, d))]
    except FileNotFoundError:
        print(f"错误：扫描 '{RESULTS_BASE_DIR}' 失败。")
        return

    if not available_backups:
        print("在结果文件夹中没有找到任何已备份的好友记录。")
        return

    print("="*50)
    print("检测到以下已备份的记录：")
    for i, backup_id in enumerate(available_backups):
        print(f"  {i + 1}. {backup_id}")
    print("="*50)

    while True:
        try:
            choice = int(input(f"请输入您想生成报告的序号 (1-{len(available_backups)}): "))
            if 1 <= choice <= len(available_backups):
                selected_id = available_backups[choice - 1]
                break
            else:
                print("无效的序号，请重新输入。")
        except ValueError:
            print("请输入数字序号。")

    selected_folder = os.path.join(RESULTS_BASE_DIR, selected_id)
    excel_file = None
    for file in os.listdir(selected_folder):
        if file.endswith('.xlsx'):
            excel_file = os.path.join(selected_folder, file)
            break
    
    if excel_file:
        generate_html_from_excel(excel_file)
    else:
        print(f"错误：在文件夹 '{selected_folder}' 中没有找到任何 .xlsx 文件。")


if __name__ == '__main__':
    main()
    input("\n按 Enter 键退出程序...")
