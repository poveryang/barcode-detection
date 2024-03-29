import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from misc import valid_pids_map


def vertices_to_bbox(vertices):
    """
    Convert vertices to bbox
    Args:
        vertices: list of [x, y] coordinates

    Returns:
        bbox: [xmin, ymin, xmax, ymax]  (left, top, right, bottom)
    """
    x_min, y_min = np.min(vertices, axis=0)
    x_max, y_max = np.max(vertices, axis=0)
    bbox = [x_min, y_min, x_max, y_max]
    return bbox


def vertices_to_rrect(vertices):
    """
    Convert box points to rotated rectangle
    Args:
        vertices: Box points, shape (4, 2)

    Returns:
        rot_rect: Rotated rectangle, [x_center, y_center, rect_w, rect_h, rot_angle]
    """

    # 1. Calculate the center of the box
    box_vertices = np.array(vertices)
    x_center, y_center = np.mean(box_vertices, axis=0)

    # 2. Calculate the rotation angle of the box
    y_s = box_vertices[:, 1] - y_center
    x_s = box_vertices[:, 0] - x_center
    angles = np.arctan2(y_s, x_s)
    rot_angle = np.rad2deg(np.mean(angles))

    # 3. Calculate the width and height of the box(Sort the points according to the angle first)
    sorted_idx = np.argsort(angles)
    box_vertices = box_vertices[sorted_idx]

    rect_w = np.mean(np.linalg.norm(box_vertices[1] - box_vertices[0])
                     + np.linalg.norm(box_vertices[3] - box_vertices[2]))
    rect_h = np.mean(np.linalg.norm(box_vertices[2] - box_vertices[1])
                     + np.linalg.norm(box_vertices[0] - box_vertices[3]))

    rot_rect = [x_center, y_center, rect_w, rect_h, rot_angle]
    return rot_rect


def parse_label_file(label_path):
    """
    Parse label
    Args:
        label_path: Label path

    Returns:
        labels: List of labels, shape (n, 5)
    """
    with open(label_path, mode='r', encoding='utf-8') as f:
        label_obj = json.load(f)

        vertices_map = defaultdict(list)
        pids_map = defaultdict(list)
        img_w, img_h = label_obj['imageWidth'], label_obj['imageHeight']
        for shape in label_obj['shapes']:
            if shape['shape_type'] != 'point' or int(shape['label']) == -1 or int(shape['label']) == 7:
                continue
            vertex = shape['points'][0]
            pid = int(shape['label'])
            group_id = shape['group_id'] if shape['group_id'] else 0

            vertices_map[group_id].append(vertex)
            pids_map[group_id].append(pid)

    return vertices_map, pids_map, img_w, img_h


def process_instances(vertices_map, pids_map, dst_format):
    # check if the group of pids is valid, convert vertices to bbox or rrect
    instances = []
    for group_id, pids in pids_map.items():
        pids.sort()
        if tuple(pids) not in valid_pids_map.keys():
            print(f"Filter invalid pids: {pids}")
            continue
        else:
            vertices = vertices_map[group_id]
            label = valid_pids_map[tuple(pids)]
            # convert vertices to bbox or rrect
            if dst_format == 'rrect':
                rrect = vertices_to_rrect(vertices)
                label_elements = rrect + [label]
            elif dst_format == 'bbox':
                bbox = vertices_to_bbox(vertices)
                label_elements = bbox + [label]
            else:
                raise ValueError(f"Unsupported format: {dst_format}")
            instances.append(label_elements)
    return instances


def filter_small_instances(instances, img_w, img_h, filter_threshold, dst_format):
    filtered_instances = []
    for instance in instances:
        if dst_format == 'rrect':
            instance_w, instance_h = instance[2], instance[3]
        elif dst_format == 'bbox':
            instance_w, instance_h = instance[2] - instance[0], instance[3] - instance[1]
        else:
            raise ValueError(f"Unsupported format: {dst_format}")
        if instance_w / img_w < filter_threshold or instance_h / img_h < filter_threshold:
            print(f"Filter small bbox: "
                  f"box size {instance_w}x{instance_h} with image size: {img_w}x{img_h}")
            continue
        filtered_instances.append(instance)
    return filtered_instances


def convert_save(data_root, dst_format='rrect', filter_threshold=0.005):
    """
    Convert label from vertices to bbox or rrect, and save to txt file
    Args:
        data_root: Root directory of dataset
        dst_format: 'bbox' or 'rrect'
        filter_threshold: Filter out the small boxes，default 0.005
    """
    data_root = Path(data_root)
    if dst_format == 'rrect':
        save_label_file = data_root.parent / 'rrect_all.txt'
    elif dst_format == 'bbox':
        save_label_file = data_root.parent / 'bbox_all.txt'
    else:
        raise ValueError(f"Unsupported format: {dst_format}")
    f = open(save_label_file, 'w', encoding='utf-8')

    label_paths = list(data_root.rglob(r"**/*.json"))
    for label_path in label_paths:
        img_relative_path = label_path.with_suffix('.png').relative_to(data_root)
        line_parts = [str(img_relative_path)]
        # 1. parse label
        vertices_map, pids_map, img_w, img_h = parse_label_file(label_path)
        # 2. process instances
        instances = process_instances(vertices_map, pids_map, dst_format)
        # 3. filter small instances
        instances = filter_small_instances(instances, img_w, img_h, filter_threshold, dst_format)
        # 4. write to file if there is at least one valid instance
        for instance in instances:
            line_parts.append(','.join([str(x) for x in instance]))
        if len(line_parts) >= 2:
            f.writelines("\t".join(line_parts) + "\n")

    f.close()


def main():
    convert_save(data_root=r"D:\Barcode-Detection-Data\data", dst_format='rrect')
    convert_save(data_root=r"D:\Barcode-Detection-Data\data", dst_format='bbox')


if __name__ == "__main__":
    main()
