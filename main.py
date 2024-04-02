import yaml
import os
import subprocess
from pathlib import Path
import shutil
import json


def main():
    print('Started script for download WSIs from GDC')
    with open('config/config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    manifest = config['manifest']
    if not os.path.exists(manifest):
        raise RuntimeError()

    output_dir = config['output_dir']
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not len(os.listdir(output_dir)) == 0:
        print(f'Directory {output_dir} is not empty, skipping download')
    else:
        print('Downloading data from GDC...')
        command = config['command']
        subprocess.run([command, "download", "-m", manifest, "-d", output_dir, "-n", "2"])

    print(f'Successfully downloaded data')

    output_path = Path(output_dir)
    renaming_strategy = config['renaming_strategy']
    print(f'Renaming strategy: {renaming_strategy}')
    if renaming_strategy == 'annotations':
        for subdir in output_path.iterdir():
            if subdir.is_dir():
                annotations_file = subdir / "annotations.txt"
                if not annotations_file.exists():
                    raise RuntimeError('Annotation file does not exists')
                else:
                    with open(annotations_file, "r") as f:
                        lines = f.readlines()
                        if not len(lines) > 1:
                            raise RuntimeError('Annotation file with wrong format')
                        else:
                            case_id = lines[1].split('\t')[3].strip()
                            for file in subdir.iterdir():
                                if file.name.endswith('.svs'):
                                    shutil.move(file, output_path / f'{case_id}.svs')
    elif renaming_strategy == 'json':
        mapping_file = config['json']
        with open(mapping_file, 'r') as file:
            data = json.load(file)
        mapping = {}
        for entry in data:
            filename = entry['file_name']
            case_id = entry['cases'][0]['case_id']
            if filename not in mapping:
                mapping[filename] = case_id
        for subdir in output_path.iterdir():
            if subdir.is_dir():
                for file in subdir.iterdir():
                    if file.name.endswith('.svs'):
                        case_id = mapping[file.name]
                        if case_id is None:
                            raise RuntimeError(f'Not found case_id for {file}')
                        shutil.move(file, output_path / f'{case_id}.svs')
    else:
        raise NotImplementedError('Renaming strategy not implemented')

    for subdir in output_path.iterdir():
        if subdir.is_dir():
            shutil.rmtree(subdir)


if __name__ == '__main__':
    main()
