import os
import sys
import shutil
import re
import json
from datetime import datetime

path = None
if(len(sys.argv) <= 1):
    print('Path is needed')
    sys.exit(1)
path = sys.argv[1]

out_path = os.path.join(path, 'out')
failed_path = os.path.join(out_path, '_failed')

if not os.path.exists(out_path):
    os.makedirs(out_path)


def get_files(path):
    return os.listdir(path)


def is_dir(path, filename):
    return os.path.isdir(os.path.join(path, filename))


def is_file(path, filename):
    return os.path.isfile(os.path.join(path, filename))


def get_files_with_extensions(path: str, extensions: list[str]):
    files = set(get_files(path))
    matched_files = set()
    for ext in extensions:
        matches = set([f for f in files if f.lower().endswith(ext)])
        matched_files = matched_files.union(matches)
        files = files.difference(matches)
    return matched_files


def get_files_with_extension(path: str, extension: str):
    return [f for f in get_files(path) if f.lower().endswith(extension)]


def get_media_files(path: str):
    return get_files_with_extensions(path, ['jpg', 'dng', 'mov', 'gif', 'mp4', 'png'])


def try_get_creation_date_from_filename(filename: str):
    regex_1 = r"20[0-9]{6}_[0-9]{6}"
    regex_2 = r"20[0-9]{6}-"
    matches = re.findall(regex_1, filename)
    if(len(matches)):
        return datetime.strptime(matches[0], '%Y%m%d_%H%M%S')
    matches = re.findall(regex_2, filename)
    if(len(matches)):
        return datetime.strptime(matches[0], '%Y%m%d-')
    return None


def get_creation_date_from_json(json_path: str):
    try:
        with open(json_path, 'r') as f:
            json_file = json.loads(f.read())
            if 'photoTakenTime' not in json_file.keys():
                raise Exception(
                    f'Json {json_path} has not photoTakenTime field', json_file)
            photoTakenTime = json_file['photoTakenTime']
            if photoTakenTime:
                creation_timestamp = int(photoTakenTime['timestamp'])
                return datetime.fromtimestamp(creation_timestamp)
    except Exception as err:
        raise err
    return None


def verify_json_linked_folder(path: str):
    files = get_files_with_extensions(
        path, ['jpg', 'dng', 'mov', 'gif', 'mp4', 'png'])
    jsons = get_files_with_extension(path, 'json')
    for file in files:
        if (not (f'{file}.json') in jsons):
            estimated_creation_date = try_get_creation_date_from_filename(file)
            if (not estimated_creation_date):
                print(f'File {file} is not repairable')


def verify_bad_metadata_folder(path: str):
    def is_bad_creation_date(date: datetime):
        is_bad = date.year == 2021 and date.month == 1 and date.day > 23
        return is_bad

    jpgs = get_files_with_extension(path, 'jpg')
    bads = 0
    for jpg in jpgs:
        creation_date_timestamp = os.path.getctime(os.path.join(path, jpg))
        creation_date = datetime.fromtimestamp(creation_date_timestamp)
        if is_bad_creation_date(creation_date):
            bads += 1
    print(f'{path.split("/")[-1]} - {bads} of {len(jpgs)} bads jpg metadata')


def verify_jsons_contains_creation_time(path):
    media_files = get_media_files(path)
    jsons = get_files_with_extension(path, 'json')
    for media in media_files:
        json_filename = f'{media}.json'
        if (json_filename in jsons):
            creation_time = get_creation_date_from_json(
                os.path.join(path, json_filename))
            if creation_time:
                pass
            else:
                print(f'{json_filename} - FAIL')


def collect_extensions(path):
    files = get_files(path)
    extensions = set()
    for f in files:
        f_path = os.path.join(path, f)
        if (os.path.isdir(f_path)):
            extensions = extensions.union(collect_extensions(f_path))
        f_splitted = f.split('.')
        if len(f_splitted) > 1:
            extensions.add(f_splitted[-1])
    return extensions


def fix_photos_in_path(path: str):
    print(f'Try to fix photos in path {path}...')
    media_files = get_media_files(path)
    jsons = get_files_with_extension(path, 'json')

    media_fixed_count = 0
    media_total = len(media_files)
    media_with_errors = []

    for media in media_files:
        folder_name = path.split('/')[-1]
        final_folder_path = os.path.join(out_path, folder_name)
        source_media_path = os.path.join(path, media)
        final_media_path = os.path.join(final_folder_path, media)

        if (not os.path.exists(final_folder_path)):
            os.makedirs(final_folder_path)

        creation_date = try_get_creation_date_from_filename(media)

        if not creation_date:
            json_filename = f'{media}.json'
            if (json_filename in jsons):
                creation_date = get_creation_date_from_json(
                    os.path.join(path, json_filename))

        if not creation_date:
            print('❌', end='')
            media_with_errors.append(media)
            failed_media_path = os.path.join(failed_path, folder_name)

            if (not os.path.exists(failed_media_path)):
                os.makedirs(failed_media_path)

            shutil.copy(source_media_path, failed_media_path)
            continue

        shutil.copy(source_media_path, final_media_path)

        formated_creation_date = creation_date.strftime(
            "%Y%m%d%H%M.%S").replace(" ", "\ ")
        command = f'touch -t {formated_creation_date} "{final_media_path}"'
        os.system(command)
        media_fixed_count += 1
        print('✅', end='')

    print('\n')
    print(
        f'Path {path.split("/")[-1]} finished! Total processed:{media_total} ✅:{media_fixed_count}  ❌: {len(media_with_errors)}')
    if len(media_with_errors):
        print(f'Some medias could not be fixed...Im sorry Dave 😢')
        for media in media_with_errors:
            print(f'❌ {os.path.join(folder_name, media)}')
    print('')
    return [media_total, media_fixed_count]


content = get_files(path)
dirs = [c for c in content if is_dir(path, c)]
files = [c for c in content if is_file(path, c)]

total = 0
total_fixes = 0
for d in dirs:
    d_path = os.path.join(path, d)
    [dir_total, fixes] = fix_photos_in_path(d_path)
    total += dir_total
    total_fixes += fixes
print(f'Done!! {total_fixes} of {total} photos are ready to shine 🎉🎊 !!!')
