import time
from aes_pkcs5.algorithms.aes_ecb_pkcs5_padding import AESECBPKCS5Padding
import json
import hashlib
import hmac
import requests
import datetime
import random
import os


def aes_encrypt(key, message):
    cipher = AESECBPKCS5Padding(key, "b64")
    encrypted = cipher.encrypt(message)
    return encrypted


def md5_encrypt(text):
    md = hashlib.md5(text.encode())  # 创建md5对象
    md5pwd = md.hexdigest()  # md5加密
    return md5pwd


def get_security(len):
    result = ""
    salt = "abcdefghijklmnopqrstuvwxyz0123456789"
    i = 0
    while i < len:
        rand = random.randint(0, 35)
        result = result + salt[rand]
        i += 1
    return result


def hmac_sha1(message, accessSecret):
    key = accessSecret.encode('utf8')  # 用户验证的关键所在
    message = message.encode('utf-8')
    hmac_obj = hmac.new(key, message, hashlib.sha1)
    return hmac_obj.hexdigest()


def get_courses(userId, accessSecret, accessId, sess: requests.Session):
    gmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
    course_url = 'https://coreapi.mosoteach.cn/ccs/joined'
    courses_message = f'GET|/ccs/joined|{userId}|{gmt_time}||'
    courses_sign = hmac_sha1(courses_message, accessSecret)

    courses_header = {
        "Date": gmt_time,
        "X-access-id": accessId,
        "X-signature": courses_sign,
        "X-client-app-id": "MTANDROID",
        "X-client-version": "5.4.30",
    }

    courses = sess.get(url=course_url, headers=courses_header).json()

    class Course:
        course_name = ""
        course_id = ""
        teacher_name = ""
        create_time = ""

    Course_list = []

    # print(courses)

    for i in courses['clazzCourses']:
        # 若班课已结束则不计入集合中
        if i['status'] == 'CLOSED':
            continue
        course_name = i['course']['name']
        # course_id = i['course']['id'] 假id
        course_id = i['id']  # 这是真id
        teacher_name = i['creater']['fullName']
        create_time = i['createTime']
        new_course = Course()
        new_course.course_name = course_name
        new_course.course_id = course_id
        new_course.teacher_name = teacher_name
        new_course.create_time = create_time
        Course_list.append(new_course)
    return Course_list


def get_status(userId, accessSecret, accessId, chosen_course_id, sess: requests.Session):
    gmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
    status_url = f'https://coreapi.mosoteach.cn/ccs/{chosen_course_id}/checkins/current'
    status_message = f'GET|/ccs/{chosen_course_id}/checkins/current|{userId}|{gmt_time}||'
    status_sign = hmac_sha1(status_message, accessSecret)
    status_header = {
        "Date": gmt_time,
        "Content-Type": "application/json",
        "X-access-id": accessId,
        "X-signature": status_sign,
        "X-client-app-id": "MTANDROID",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230804.001)",
        "X-client-version": "5.4.30",
    }
    print("当前时间: " + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    status_info = sess.get(url=status_url, headers=status_header).text
    status_info = json.loads(status_info)
    print("签到状态:", status_info)
    return status_info


def login(account, password, sess: requests.Session):
    gmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
    login_url = "https://coreapi.mosoteach.cn/passports/account-login"
    login_key = "526EBA802E6FCF44661DE4393A82ABDA"

    login_security = get_security(32)
    login_data_string = '{"account":"' + account + '","password":"' + password + '"}'
    login_message = f"POST|/passports/account-login|MTANDROID|{gmt_time}||{md5_encrypt(login_data_string)}"
    login_signatrue = hmac_sha1(login_message, login_key)
    login_data = aes_encrypt(login_key, login_data_string)
    login_headers = {
        "Date": gmt_time,
        "Content-Type": "application/json",
        "X-access-id": "MTANDROID",  # 此时还没获取到用户的accessid,默认使用MTANDROID
        "X-signature": login_signatrue,
        "X-client-app-id": "MTANDROID",
        "X-client-version": "5.4.30",
        "X-security": login_security,
    }
    login_res = sess.post(url=login_url, headers=login_headers, data=login_data)
    try:
        userId = login_res.json()['user']['userId']
        accessSecret = login_res.json()['user']['accessSecret']
        accessId = login_res.json()['user']['accessId']
        return (userId, accessSecret, accessId)
    except:
        return ()


def get_pos(chosen_course_id):
    if not os.path.exists("./pos.json"):
        abs_path = os.path.abspath("./pos.json")
        with open("./pos.json", mode='w', encoding="utf-8") as fp:
            print(
                f"位置配置文件已创建,路径为: {abs_path} ,可以自行前往配置!")
            pos = {
                "lats": {
                },
                "lngs": {
                }
            }
            json.dump(pos, fp)
    with open("./pos.json", mode='r', encoding="utf-8") as fp:
        try:
            pos = json.load(fp)
            lats = pos['lats']
            lngs = pos['lngs']
        except:
            print("签到位置配置文件有问题, 已删除, 请重新打开本程序!")
            fp.close()
            os.remove("./pos.json")
            time.sleep(10)
            exit()
        try:
            lat = lats[chosen_course_id]
            lng = lngs[chosen_course_id]
            print("签到纬度: " + lat, "签到经度: " + lng)
        except:
            lat = ''
            lng = ''
            # print("暂未获取到该课程的位置信息, 请自行补充!")
    print("如果你不知道如何获取经纬度, 请前往这里 -> https://api.map.baidu.com/lbsapi/getpoint/index.html")
    if lat == '' or lng == '':
        flag = input(
            "暂未获取到该课程的位置信息!\n如果你需要对选择课程位置信息进行补充, 请输入pos并回车, 或输入其他进入签到界面: ")
    else:
        flag = input(
            "目前该课程已有位置信息, 如果你需要对选择课程位置信息进行修改, 请输入pos并回车, 或输入其他进入签到界面: ")

    if flag == 'pos':
        while True:
            lat = input("请输入纬度: ")
            lng = input("请输入经度: ")
            try:
                float(lat)
                float(lng)
                break
            except:
                print("位置信息必须是纯数字!")
        with open("./pos.json", mode='r+', encoding="utf-8") as fp:
            pos = json.load(fp)
            pos['lats'][chosen_course_id] = lat
            pos['lngs'][chosen_course_id] = lng
            fp.close()
        # 这里这样写是因为第一次将pos.json里的数据读取出来放到pos这个对象上,新写入的数据同时也放到了pos对象上
        # 随后再w模式打开pos.json,将这个带有新数据和旧数据的pos对象写入回pos.json里
        with open("./pos.json", mode='w', encoding="utf-8") as fp:
            json.dump(pos, fp)
        print('位置信息已添加')


# def check(account, password):
if __name__ == '__main__':
    account = ''
    password = ''
    sess = requests.session()
    gmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
    login_res = login(account=account, password=password, sess=sess)
    try:
        userId = login_res[0]
        accessSecret = login_res[1]
        accessId = login_res[2]
    except:
        print("登录失败, 请检查账号密码是否正确")
        exit()

    Course_list = get_courses(userId, accessSecret, accessId, sess)

    for i in Course_list:
        print(f"课程名称: {i.course_name}  课程id: {i.course_id}  教师名称: {i.teacher_name}")

    # 签到:
    flag = True
    chosen_course_id = ''
    while flag:
        chosen_course_id = input("请输入课程ID: ")
        for i in Course_list:
            if (i.course_id == chosen_course_id):
                print("当前选择签到课程:", i.course_name)
                flag = False
        if flag:
            print("课程ID输入错误, 请重新输入!")

    get_pos(chosen_course_id=chosen_course_id)

    while True:
        flag = input("请选择是上午签到还是下午签到, 输入1上午签到, 输入2下午签到: ")
        if flag == "1":
            start_time = "08:00"
            break_time = "12:00"
            break
        elif flag == "2":
            start_time = "12:50"
            break_time = "16:30"
            break
        else:
            print("输入错误, 请重新输入!")

    while True:
        now_time = datetime.datetime.now()
        if now_time.strftime("%H:%M") < start_time:
            print("尚未到设置的开始时间, 当前时间: " + str(now_time.strftime('%Y-%m-%d %H:%M:%S')))
            print("等待中...")
            time.sleep(60)
            continue
        if now_time.strftime("%H:%M") > break_time:
            break
        status_info = get_status(userId, accessSecret, accessId, chosen_course_id, sess)

        checkin_id = ''
        with open("./pos.json", mode='r', encoding="utf-8") as fp:
            try:
                pos = json.load(fp)
                lats = pos['lats']
                lngs = pos['lngs']
            except:
                print("签到位置配置文件有问题, 已删除, 请重新打开本程序!")
                fp.close()
                os.remove("./pos.json")
                time.sleep(10)
                exit()
            try:
                lat = lats[chosen_course_id]
                lng = lngs[chosen_course_id]
                print("签到纬度: " + lat, "签到经度: " + lng)
            except:
                lat = ''
                lng = ''
                print("暂未获取到该课程的位置信息, 请自行补充!")

        if status_info['status']:
            if status_info['checkin']['type'] == 'CLOCKIN':
                print("限时签到!")
                clockin_url = "https://api.mosoteach.cn/mssvc/index.php/cc_clockin/clockin"
                clockin_message = f'https://api.mosoteach.cn/mssvc/index.php/cc_clockin/clockin|{userId}|{gmt_time}|{md5_encrypt(f"cc_id={chosen_course_id}").upper()}'
                clockin_sign = hmac_sha1(clockin_message, accessSecret)
                clockin_headers = {
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230804.001)",
                    "Date": gmt_time,
                    "X-device-code": "bc55d279_8a7b_4a43_80e5_e6f8776d9424",
                    "X-mssvc-signature": clockin_sign,
                    "X-mssvc-access-id": accessId,
                    "X-app-id": "MTANDROID",
                    "X-app-version": "5.4.33",
                    "X-dpr": "3.5",
                    "X-app-machine": "2210132C",
                    "X-app-system-version": "14",
                    "X-mssvc-sec-ts": "1687060278",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                }
                clockin_data = {
                    "cc_id": chosen_course_id,
                }
                clockin_res = sess.post(url=clockin_url, headers=clockin_headers, data=clockin_data)
                print(clockin_res.text)
            else:
                print("签到已开启! 开启时间: " + status_info['checkin']['openTime'])
                checkin_id = str(status_info['checkin']['id'])
                print("签到ID: " + checkin_id)

                checkin_id = str(status_info['checkin']['id'])

                checkin_url = 'https://checkin.mosoteach.cn:19528/checkin'

                checkin_message = f'https://checkin.mosoteach.cn:19528/checkin|{userId}|{gmt_time}'

                checkin_sign = hmac_sha1(checkin_message, accessSecret)

                checkin_headers = {
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230804.001)",
                    "Date": gmt_time,
                    "X-device-code": "bc55d279_8a7b_4a43_80e5_e6f8776d9424",
                    "X-mssvc-signature": checkin_sign,
                    "X-mssvc-access-id": accessId,
                    "X-app-id": "MTANDROID",
                    "X-app-version": "5.4.33",
                    "X-dpr": "3.5",
                    "X-app-machine": "2210132C",
                    "X-app-system-version": "14",
                    "X-mssvc-sec-ts": "1687060278",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                }

                checkin_data = {
                    'checkin_id': checkin_id,
                    'report_pos_flag': 'Y',
                    'lat': lat,
                    'lng': lng,
                }
                print("签到纬度: " + lat, "签到经度: " + lng)
                checkin_res = sess.post(url=checkin_url, headers=checkin_headers, data=checkin_data)
                re = eval("u" + "\'" + checkin_res.text + "\'")
                print(re)
                result_code = json.loads(checkin_res.text)['result_code']
                if result_code == 0:
                    print("签到已成功,请等待重复签到确保签到成功")
                    time.sleep(2)
                elif result_code == 2409:
                    print("重复签到成功")
                elif result_code == 2404:
                    print("签到尚未开始!")
        time.sleep(7 + random.randint(0, 3))
