# 导入必要的库
import configparser
import os
import requests
import time
import re
import json
from tqdm import tqdm
import pandas as pd
import platform
import subprocess
from PIL import Image
import qrcode
from pyzbar.pyzbar import decode

# ==============================================================================
# 模块 1: 配置模块
# ==============================================================================
config = configparser.ConfigParser()
config_path = './resource/config/config.ini'
if not os.path.exists(os.path.dirname(config_path)):
    os.makedirs(os.path.dirname(config_path))
if not os.path.exists(config_path):
    config['File'] = {
        'temp': './resource/temp/',
        'user': './resource/user/',
        'result': './resource/result/'
    }
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    print(f"创建了默认配置文件: {config_path}")

config.read(config_path)

temp_path = config.get('File', 'temp')
user_path = config.get('File', 'user')
result_path = config.get('File', 'result')

def save_user(cookies):
    with open(os.path.join(user_path, cookies.get('uin')), 'w') as f:
        f.write(str(cookies))

def init_flooder():
    for path in [temp_path, user_path, result_path]:
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"创建目录: {path}")

def read_files_in_folder():
    if not os.path.exists(user_path) or not os.listdir(user_path):
        return None
    files = os.listdir(user_path)
    print("已登录用户列表:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")
    while True:
        try:
            choice = int(input("请选择要登录的用户序号 (重新登录请输入0): "))
            if 0 <= choice <= len(files):
                return None if choice == 0 else os.path.join(user_path, files[choice - 1])
            else:
                print("无效的选择，请重新输入。")
        except ValueError:
            print("无效的选择，请重新输入。")

# ==============================================================================
# 模块 2: 登录与通用工具
# ==============================================================================
cookies = None
g_tk = None
login_uin = None
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
}

def bkn(pSkey):
    t, n, o = 5381, 0, len(pSkey)
    while n < o:
        t += (t << 5) + ord(pSkey[n])
        n += 1
    return t & 2147483647

def ptqrToken(qrsig):
    n, i, e = len(qrsig), 0, 0
    while n > i:
        e += (e << 5) + ord(qrsig[i])
        i += 1
    return 2147483647 & e

def QR():
    url = 'https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.8692955245720428&daid=5&pt_3rd_aid=0'
    try:
        r = requests.get(url )
        qrsig = requests.utils.dict_from_cookiejar(r.cookies).get('qrsig')
        qr_path = os.path.join(temp_path, 'QR.png')
        with open(qr_path, 'wb') as f:
            f.write(r.content)
        im = Image.open(qr_path)
        print(time.strftime('%H:%M:%S'), '登录二维码获取成功，请扫描：')
        qr_code = qrcode.QRCode()
        qr_code.add_data(decode(im)[0].data.decode('utf-8'))
        qr_code.print_ascii(invert=True)
        return qrsig
    except Exception as e:
        print(f"获取二维码失败: {e}")
        return None

def do_login():
    global cookies, g_tk, login_uin
    init_flooder()
    user_file_path = read_files_in_folder()
    if user_file_path:
        with open(user_file_path, 'r') as file:
            print("检测到已保存的登录信息，将使用该信息登录。")
            cookies = eval(file.read())
    else:
        qrsig = QR()
        if not qrsig: return False
        ptqrtoken = ptqrToken(qrsig)
        while True:
            url = f'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html&ptqrtoken={ptqrtoken}&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-{time.time( )}&js_ver=21011310&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&'
            cookies_jar = {'qrsig': qrsig}
            try:
                r = requests.get(url, cookies=cookies_jar, timeout=10)
                if '二维码未失效' in r.text: time.sleep(2)
                elif '二维码认证中' in r.text: print(time.strftime('%H:%M:%S'), '二维码认证中...')
                elif '二维码已失效' in r.text: print(time.strftime('%H:%M:%S'), '二维码已失效，请重新运行程序'); return False
                else:
                    match = re.search(r'ptsigx=(.*?)&', r.text)
                    if not match:
                        time.sleep(1)
                        continue
                    print(time.strftime('%H:%M:%S'), '登录成功!')
                    cookies_jar = requests.utils.dict_from_cookiejar(r.cookies)
                    uin = cookies_jar.get('uin')
                    sigx = match.group(1)
                    check_sig_url = f'https://ptlogin2.qzone.qq.com/check_sig?pttype=1&uin={uin}&service=ptqrlogin&nodirect=0&ptsigx={sigx}&s_url=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html&f_url=&ptlang=2052&ptredirect=100&aid=549000912&daid=5&j_later=0&low_login_hour=0&regmaster=0&pt_login_type=3&pt_aid=0&pt_aaid=16&pt_light=0&pt_3rd_aid=0'
                    r = requests.get(check_sig_url, cookies=cookies_jar, allow_redirects=False )
                    cookies = requests.utils.dict_from_cookiejar(r.cookies)
                    save_user(cookies)
                    break
            except Exception as e:
                print(f"登录过程中发生错误: {e}")
                time.sleep(3)
    
    if not cookies: return False
    
    g_tk = bkn(cookies.get('p_skey'))
    login_uin = re.sub(r'o0*', '', cookies.get('uin'))
    
    try:
        url = f'https://r.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?g_tk={g_tk}&uins={login_uin}'
        response = requests.get(url, headers=headers, cookies=cookies )
        info_str = response.content.decode('GBK').strip().lstrip('portraitCallBack(').rstrip(');')
        user_info = json.loads(info_str)
        user_nickname = user_info[login_uin][6]
        print(f"用户 <{user_nickname}> ({login_uin}) 登录成功！")
        return True
    except Exception as e:
        print(f"获取登录用户信息失败: {e}")
        return False

def open_file_or_path(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception:
        print(f"无法自动打开文件夹，请手动访问：{path}")

# ==============================================================================
# 模块 3: 获取好友动态的核心功能
# ==============================================================================
def get_friend_message(target_uin, start, count):
    url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6'
    params = {'uin': target_uin, 'ftype': '0', 'sort': '0', 'pos': start, 'num': count, 'g_tk': g_tk, 'format': 'jsonp'}
    try:
        response = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=15 )
        return response
    except requests.Timeout:
        print(f"获取动态列表超时 (pos={start})")
        return None

def get_friend_message_count(target_uin):
    print("正在获取好友动态总数...")
    response = get_friend_message(target_uin, 0, 1)
    if response:
        try:
            json_str = response.text.strip().lstrip('_preloadCallback(').rstrip(');')
            data = json.loads(json_str)
            total = data.get('total')
            if total is not None:
                print(f"获取成功，好友动态总数为: {total}")
                return total
            elif data.get('message') == '对不起,主人设置了保密,您没有权限查看':
                print("错误：您没有权限查看该好友的动态。")
                return 0
            else:
                print("未能获取到动态总数，可能对方没有发表过动态或返回数据异常。")
                return 0
        except Exception as e:
            print(f"解析总数失败: {e}")
            return 0
    return 0

def sanitize_filename(text):
    """清理文件名中的非法字符，并截取长度"""
    if not text:
        return ""
    # 替换掉换行和回车符
    text = text.replace('\n', ' ').replace('\r', '')
    # 替换掉其他不适合做文件名的字符
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', text)
    # 截取前30个字符以防文件名过长
    return sanitized[:30]

def run_friend_scrape_mode():
    """主程序逻辑：获取好友动态、下载媒体、保存Excel"""
    target_uin = input("请输入您要获取动态的好友QQ号: ").strip()
    
    total_count = get_friend_message_count(target_uin)
    if total_count == 0: return

    all_posts_data = []
    batch_size = 20
    with tqdm(total=total_count, desc='获取好友动态') as pbar:
        for i in range(0, total_count, batch_size):
            response = get_friend_message(target_uin, i, batch_size)
            if not response:
                pbar.update(min(batch_size, total_count - pbar.n))
                continue
            try:
                json_str = response.text.strip().lstrip('_preloadCallback(').rstrip(');')
                data = json.loads(json_str)
                if 'msglist' in data and data['msglist'] is not None:
                    for msg in data['msglist']:
                        all_posts_data.append({
                            'tid': msg.get('tid'), 
                            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg['created_time'])),
                            'content': msg.get('content', ''), 
                            'pictures': [p.get('url2') or p.get('url1', '') for p in msg.get('pic', [])], 
                            'video_url': msg.get('video_info', [{}])[0].get('url', ''),
                        })
                        pbar.update(1)
                else:
                    pbar.update(min(batch_size, total_count - pbar.n))
            except Exception as e:
                print(f"解析位置 {i} 的数据时出错: {e}")
                pbar.update(min(batch_size, total_count - pbar.n))
            time.sleep(0.5)

    user_save_path = os.path.join(result_path, target_uin)
    pic_save_path = os.path.join(user_save_path, 'pic')
    video_save_path = os.path.join(user_save_path, 'video')
    os.makedirs(pic_save_path, exist_ok=True)
    os.makedirs(video_save_path, exist_ok=True)

    final_data_for_excel = []

    for post in tqdm(all_posts_data, desc="下载媒体文件并整理数据"):
        post_time_str = post['time']
        post_content_sanitized = sanitize_filename(post['content'])
        
        local_pic_paths = []
        for i, pic_link in enumerate(post['pictures']):
            try:
                pic_name = f"{post_time_str.replace(':', '-')}_{post_content_sanitized}_{i}.jpg"
                pic_response = requests.get(pic_link, timeout=20)
                if pic_response.status_code == 200:
                    local_path = os.path.join(pic_save_path, pic_name)
                    with open(local_path, 'wb') as f: f.write(pic_response.content)
                    local_pic_paths.append(os.path.join('pic', pic_name))
            except Exception as e: print(f"下载图片失败: {pic_link}, 错误: {e}")
        
        local_video_path = ""
        if post['video_url']:
            try:
                video_name = f"{post_time_str.replace(':', '-')}_{post_content_sanitized}.mp4"
                video_response = requests.get(post['video_url'], timeout=60, stream=True)
                if video_response.status_code == 200:
                    local_path = os.path.join(video_save_path, video_name)
                    with open(local_path, 'wb') as f:
                        for chunk in video_response.iter_content(chunk_size=8192): f.write(chunk)
                    local_video_path = os.path.join('video', video_name)
            except Exception as e: print(f"下载视频失败: {post['video_url']}, 错误: {e}")
        
        final_data_for_excel.append({
            'tid': post['tid'],
            '时间': post['time'],
            '内容': post['content'],
            '图片网络链接': ', '.join(post['pictures']),
            '视频网络链接': post['video_url'],
            '本地图片路径': ', '.join(local_pic_paths),
            '本地视频路径': local_video_path
        })

    df = pd.DataFrame(final_data_for_excel)
    excel_path = os.path.join(user_save_path, f'{target_uin}.xlsx')
    df.to_excel(excel_path, index=False)
    print(f'\n数据处理完成！Excel已保存至: {excel_path}')
    print("现在，您可以使用 report.py 脚本来为这份新的Excel文件生成报告了。")
    open_file_or_path(user_save_path)

# ==============================================================================
# 模块 4: 主程序入口
# ==============================================================================
if __name__ == '__main__':
    # 解决命名冲突的提示
    if os.path.exists('html.py'):
        print("\n" + "="*60)
        print("!! 重要警告：检测到命名冲突 !!")
        print("您的文件夹中存在一个名为 'html.py' 的文件。")
        print("这个文件名与Python系统库冲突，会导致 'ModuleNotFoundError'。")
        print("请立即将其重命名为 'report_generator.py' 或其他名称。")
        print("="*60 + "\n")
        input("按 Enter 键退出程序...")
        exit()

    if do_login():
        run_friend_scrape_mode()
    else:
        input("登录失败，按 Enter 键退出...")
    
    input("\n所有任务完成，按 Enter 键退出程序...")
