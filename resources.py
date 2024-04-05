import datetime
import json

import requests

from crypt import hmac_sha1, md5_encrypt


def complete_resources(userId, accessSecret, accessId, Course_list: list, sess: requests.Session):
    for i in Course_list:
        gmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %X GMT")
        print("当前选择刷资源课程:", i.course_name)
        chosen_course_id = i.course_id
        resource_url = f'https://coreapi.mosoteach.cn/ccs/{chosen_course_id}/resources?roleId=2'

        resource_message = f"GET|/ccs/{chosen_course_id}/resources|{userId}|{gmt_time}|roleId=2|"

        resource_sign = hmac_sha1(resource_message, accessSecret)

        resource_headers = {
            "Accept-Encoding": "gzip;q=0.7,*;q=0.7",
            "Date": gmt_time,
            "Content-Type": "application/json",
            "Accept-Language": "zh-CN",
            "X-access-id": accessId,
            "X-signature": resource_sign,
            "X-client-app-id": "MTANDROID",
            "X-client-version": "5.4.33",
            "X-client-dpr": "3.5",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230804.001)",
        }

        resource_res = sess.get(url=resource_url, headers=resource_headers)
        # print(resource_res.text)
        resources_list = resource_res.json()['resources']
        # print(resources_list)

        for resource in resources_list:
            resource_name = resource['name']
            entity_id = resource['id']
            entity_type = 'RESOURCE'
            is_screenx = 'N'
            view_type = 'VIEW'
            view_url = 'https://api.mosoteach.cn/mssvc/index.php/viewer/get_viewer'
            md5_id = md5_encrypt(
                f'entity_id={entity_id}|entity_type={entity_type}|is_screenx={is_screenx}|type={view_type}').upper()
            view_message = f'https://api.mosoteach.cn/mssvc/index.php/viewer/get_viewer|{userId}|{gmt_time}|{md5_id}'
            view_sign = hmac_sha1(view_message, accessSecret)

            view_headers = {
                "Accept-Encoding": "gzip;q=0.7,*;q=0.7",
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230804.001)",
                "X-scheme": "https",
                "Date": gmt_time,
                "X-mssvc-signature": view_sign,
                "X-mssvc-access-id": accessId,
                "X-app-id": "MTANDROID",
                "X-app-version": "5.4.33",
                "X-dpr": "3.5",
                "X-app-machine": "2210132C",
                "X-app-system-version": "14",
                "X-mssvc-sec-ts": "1687060278",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Content-Length": "90",
            }

            view_data = {
                'entity_id': entity_id,
                'entity_type': entity_type,
                'is_screenx': is_screenx,
                'type': view_type,
            }

            view_res = sess.post(url=view_url, headers=view_headers, data=view_data)
            print(resource_name)
            # print(resource_name + ": \n", json.loads(view_res.text))
            if json.loads(view_res.text)['data']['mime_type'] == 'video/mp4':
                duration = str(json.loads(view_res.text)['data']['meta_duration'])
                video_url = 'https://api.mosoteach.cn/mssvc/index.php/cc_record/save_res_video_record'
                video_md5 = md5_encrypt(
                    f'clazz_course_id={chosen_course_id}|current_watch_to={duration}|duration={duration}|res_id={entity_id}|watch_to={duration}').upper()
                video_message = f'https://api.mosoteach.cn/mssvc/index.php/cc_record/save_res_video_record|{userId}|{gmt_time}|{video_md5}'
                video_sign = hmac_sha1(video_message, accessSecret)
                video_headers = {
                    "Accept-Encoding": "gzip;q=0.7,*;q=0.7",
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230804.001)",
                    "X-scheme": "https",
                    "Date": gmt_time,
                    "X-mssvc-signature": video_sign,
                    "X-mssvc-access-id": accessId,
                    "X-app-id": "MTANDROID",
                    "X-app-version": "5.4.33",
                    "X-dpr": "3.5",
                    "X-app-machine": "2210132C",
                    "X-app-system-version": "14",
                    "X-mssvc-sec-ts": "1687060278",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                }
                video_data = {
                    "clazz_course_id": chosen_course_id,
                    "current_watch_to": duration,
                    "duration": duration,
                    "res_id": entity_id,
                    "watch_to": duration
                }
                video_res = sess.post(url=video_url, headers=video_headers, data=video_data)
                # print(video_res.text)
    print("刷资源完成, 可自行退出 -- By UmiK233")
